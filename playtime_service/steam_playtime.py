import asyncio
import logging
from typing import Sequence

import aiohttp
import yarl

_STEAM_PLAYER_API_BASE_URL = yarl.URL("https://api.steampowered.com/")


class SteamConnectAsync:
    def __init__(self, *, api_key: str, timeout: float, max_chunk_size: int = 100) -> None:
        self.api_key: str = api_key
        self.timeout: float = timeout
        self.max_chunk_size: int = max_chunk_size

        client_timeout = aiohttp.ClientTimeout(self.timeout)
        self._session: aiohttp.ClientSession = aiohttp.ClientSession(_STEAM_PLAYER_API_BASE_URL, timeout=client_timeout)

    def __del__(self):
        if not self._session.closed:
            loop = asyncio.get_event_loop()
            loop.create_task(self.close())

    async def close(self):
        await self._session.close()

    async def get_game_playtime(self, *, steam_id, game_id):
        games = await self.get_recently_played_games(steam_id=steam_id)

        if games:
            playtime = self._search_game_in_list(game_list=games, game_id=game_id)
            if playtime:
                return playtime

        games = await self.get_owned_games(steam_id=steam_id)

        if games:
            playtime = self._search_game_in_list(game_list=games, game_id=game_id)
            if playtime:
                return playtime

        return None

    async def get_recently_played_games(self, *, steam_id):
        params = {"steamid": steam_id, "key": self.api_key}

        try:
            async with self._session.get("IPlayerService/GetRecentlyPlayedGames/v1/", params=params) as response:
                if response.status != 200:
                    logging.warning(
                        f"Неверный статус код при получении списка игр у пользователя {steam_id},"
                        f" статус код {response.status}"
                    )
                    return None

                data = await response.json()

                return data["response"]["games"]
        except aiohttp.ClientError as e:
            logging.error(f"Ошибка при получении списка последних сыгранных игр у пользователя {steam_id}, ошибка: {e}")
            return None
        except KeyError as e:
            logging.error(f"У пользователя {steam_id} не найдены игры. KeyError {e}")

    async def get_owned_games(self, *, steam_id):
        params = {"steamid": steam_id, "include_appinfo": "true", "key": self.api_key}

        try:
            async with self._session.get("IPlayerService/GetOwnedGames/v1/", params=params) as response:
                if response.status != 200:
                    logging.warning(
                        f"Неверный статус код при получении списка игр у пользователя {steam_id},"
                        f" статус код {response.status}"
                    )
                    return None

                data = await response.json()

                return data["response"]["games"]
        except aiohttp.ClientError as e:
            logging.error(f"Ошибка при получении списка игр у пользователя {steam_id}, ошибка: {e}")
            return None
        except KeyError as e:
            logging.error(f"У пользователя {steam_id} не найдены игры. KeyError {e}")

    async def get_player_data(self, *, steam_id: str) -> dict[str, str | int | float] | None:
        try:
            players = await self.get_players_data(steam_ids=[steam_id])
            if players:
                return players[0]
            else:
                return None
        except IndexError as e:
            logging.error(f"Ошибка при получении информации о пользователе {steam_id}, ошибка: {e}")
            return None

    async def get_players_data(self, *, steam_ids: Sequence[str]) -> list[dict[str, str | int | float]] | None:
        steam_ids_chunks = [
            steam_ids[i : i + self.max_chunk_size] for i in range(0, len(steam_ids), self.max_chunk_size)
        ]

        ret_data = []
        for ids_chunk in steam_ids_chunks:
            params = {"steamids": ",".join(ids_chunk), "key": self.api_key}

            try:
                async with self._session.get("ISteamUser/GetPlayerSummaries/v1/", params=params) as response:
                    if response.status != 200:
                        logging.warning(
                            f"Неверный статус код при получении информации о пользователях {ids_chunk}:"
                            f" {response.status}"
                        )
                        return None

                    ret_data.extend((await response.json())["response"]["players"]["player"])

            except (aiohttp.ClientError, KeyError, IndexError) as e:
                logging.error(f"Ошибка при получении пользователях {steam_ids}, ошибка: {type(e)} {e}")
                return None

        return ret_data

    def _search_game_in_list(self, *, game_list, game_id) -> None | int:
        for game in game_list:
            if game["appid"] == game_id:
                playtime = game.get("playtime_forever")
                if playtime == 0:
                    return None
                return playtime
