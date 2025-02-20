import asyncio
import logging
from typing import Iterable

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import transaction
from steam_playtime import SteamConnectAsync

from .models import Playtime


def update_or_create_playtime(*, steam_id, game_id, steam_playtime=None, bm_playtime=None):
    # Минуты в секунды
    _steam_playtime = steam_playtime
    if steam_playtime is not None:
        _steam_playtime = steam_playtime * 60

    playtime, created = Playtime.objects.get_or_create(
        steam_id=steam_id, game_id=game_id, defaults={"bm_playtime": bm_playtime, "steam_playtime": _steam_playtime}
    )

    if created:
        return playtime

    # Сохранение последних измененных данных если steam_id уже существовал
    edited = False
    if _steam_playtime is not None:
        playtime.steam_playtime = _steam_playtime
        edited = True
    if bm_playtime is not None:
        playtime.bm_playtime = bm_playtime
        edited = True

    if edited:
        playtime.save()

    return playtime


async def retrieve_playtimes_from_steam(*, steam_ids: list, game_id: int) -> list[int | None]:
    sca = SteamConnectAsync(api_key=settings.STEAM_API_KEY, timeout=settings.STEAM_API_TIMEOUT)

    tasks = []
    for steam_id in steam_ids:
        tasks.append(asyncio.create_task(sca.get_game_playtime(steam_id=steam_id, game_id=game_id)))

    playtime_task_results: list[int | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)

    await sca.close()

    for index, steam_id_with_result in enumerate(zip(steam_ids, playtime_task_results)):
        steam_id, result = steam_id_with_result
        if isinstance(result, Exception):
            logging.error(f"Error fetching game playtime for steam_id {steam_id}: {result}", exc_info=result)
            playtime_task_results[index] = None  # type: ignore

    return playtime_task_results  # type: ignore


def get_playtimes_from_db(*, steam_ids: Iterable[str], game_id: int):
    return Playtime.objects.filter(steam_id__in=steam_ids, game_id=game_id)


def get_playtime_with_update(*, steam_id: str, game_id: int):
    new_steam_playtime = async_to_sync(retrieve_playtimes_from_steam)(steam_ids=[steam_id], game_id=game_id)[0]

    return update_or_create_playtime(steam_id=steam_id, game_id=game_id, steam_playtime=new_steam_playtime)


def get_playtimes_with_update(*, steam_ids: Iterable[str], game_id: int):
    unique_steam_ids = list(set(steam_ids))
    new_steam_playtimes = async_to_sync(retrieve_playtimes_from_steam)(steam_ids=unique_steam_ids, game_id=game_id)

    updated_playtimes = []
    with transaction.atomic():
        for steam_id, playtime in zip(unique_steam_ids, new_steam_playtimes):
            updated_playtimes.append(
                update_or_create_playtime(steam_id=steam_id, game_id=game_id, steam_playtime=playtime)
            )

    return updated_playtimes


def get_playtimes_with_search_unknown(*, steam_ids: Iterable[str], game_id: int):
    steam_ids_set = set(steam_ids)

    db_playtimes = get_playtimes_from_db(steam_ids=steam_ids_set, game_id=game_id)

    founded_steam_ids = [playtime.steam_id for playtime in db_playtimes]

    if len(steam_ids_set) == len(founded_steam_ids):
        return db_playtimes

    not_founded_steam_ids = list(steam_ids_set.difference(founded_steam_ids))

    new_playtimes_from_steam = async_to_sync(retrieve_playtimes_from_steam)(
        steam_ids=not_founded_steam_ids, game_id=game_id
    )

    new_db_playtimes = []
    with transaction.atomic():
        for steam_id, playtime in zip(not_founded_steam_ids, new_playtimes_from_steam):
            new_db_playtimes.append(
                update_or_create_playtime(steam_id=steam_id, game_id=game_id, steam_playtime=playtime)
            )

    return list(db_playtimes) + new_db_playtimes
