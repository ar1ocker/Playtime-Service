# Playtime-Service

Сервис который получает и хранит игровое время игроков в определенной игре

Сервис получает игровое время через вебхуки от Battemetrics (с проверкой HMAC)
Сервис самостоятельно получает игровое время указанное в Steam через официальный API при запросе

API ручки:

```http://your-site.ru/get-playtime/<str:path>/```

```http://your-site.ru/set-playtime/bm/<str:path>/```

Где \<path\> это взятый из базы путь для которого установлен HMAC ключ

![изображение](https://github.com/user-attachments/assets/a2c3d8b9-06df-40cf-8c56-fb29db063001)
![изображение](https://github.com/user-attachments/assets/113a3a73-4d0d-47f9-91ef-f31d7edcff75)

HMAC проверяется на обоих API, разница лишь в том, что для Battlemetrics проверяется timestamp в HMAC, а для запроса get-playtime - нет
[https://learn.battlemetrics.com/article/47-webhooks#x-signature](https://learn.battlemetrics.com/article/47-webhooks#x-signature)

При вычислении HMAC должен быть использован алгоритм SHA256, а сам HMAC должен быть вставлен как hex в заголовок X-SIGNATURE

## Запускаем

+ Копируем и переименовываем configs/playtime/config-example.toml в configs/playtime/config.toml
+ Вводим свои значения везде куда нужно (секретный ключ для Django, пароль от Postgres, [ключ для Steam](https://steamcommunity.com/dev))
+ Копируем и переименовываем configs/postgres/postgres-example.env в configs/postgres/postgres.env
+ Вводим пароль от Postgres, такой же как и до этого
+ `docker compose up -d`

## Запросы

От Battlemetrics Webhook должен быть вот такого вида

```json
{
  "steam_id": "{{player.steamID}}",
  "playtime": "{{player.game.timePlayed}}",
  "game_id": 393380
}
```

Ключ для HMAC вам также даст сам Battlemetrics при вводе Webhook

От скриптов запрос должен быть вот такого вида

```json
{
  "steam_ids": ["7600000000000123", "7600000000000123", "7600000000000123"],
  "game_id": 393380,
  "is_need_update": false
}
```

is_need_update - опционален, время из Steam будет запрашиваться в двух случаях, когда is_need_update == True или когда Steam ID не найден
