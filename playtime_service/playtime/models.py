from django.db import models


class Playtime(models.Model):
    steam_id = models.CharField("Steam ID 64", max_length=18)
    game_id = models.IntegerField("Game ID")
    steam_playtime = models.IntegerField("Игровое время по Steam", null=True, blank=True)
    bm_playtime = models.IntegerField("Игровое время по Battlemetrics", null=True, blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата изменения", auto_now=True)

    def __str__(self):
        steam_hours = int(self.steam_playtime / 60 / 60) if self.steam_playtime else "-"
        bm_hours = int(self.bm_playtime / 60 / 60) if self.bm_playtime else "-"
        return f"{self.steam_id} - ST: {steam_hours}, BM: {bm_hours}"

    class Meta:
        verbose_name = "'Игровое время'"
        verbose_name_plural = "1. Игровое время игроков"

        unique_together = ["steam_id", "game_id"]


class BattlemetricsSetPath(models.Model):
    enabled = models.BooleanField("Включен", default=False)
    path = models.CharField("Путь", max_length=255, unique=True)
    hmac_secret_key = models.CharField("HMAC ключ", max_length=255)
    fixed_game_id = models.IntegerField("Зафиксированный Game ID", null=True, blank=True)

    class Meta:
        verbose_name = "'Подключение Battlemetrics'"
        verbose_name_plural = "2. Подключения Battlemetrics"

    def __str__(self):
        return f"'{self.pk} - {self.path}'"

    def clean(self):
        self.path = self.path.lower().strip().replace(" ", "-")


class PlaytimeGetPath(models.Model):
    enabled = models.BooleanField("Включен", default=False)
    path = models.CharField("Путь", max_length=255, unique=True)
    hmac_secret_key = models.CharField("HMAC ключ", max_length=255)
    fixed_game_id = models.IntegerField("Зафиксированный Game ID", null=True, blank=True)

    class Meta:
        verbose_name = "'Подключение скриптов'"
        verbose_name_plural = "3. Подключения скриптов"

    def __str__(self) -> str:
        return f"'{self.pk} - {self.path}'"

    def clean(self):
        self.path = self.path.lower().strip().replace(" ", "-")
