from django.contrib import admin

from .models import BattlemetricsSetPath, Playtime, PlaytimeGetPath


@admin.register(Playtime)
class PlaytimeAdmin(admin.ModelAdmin):
    fields = [
        "id",
        "steam_id",
        "game_id",
        "steam_playtime",
        "get_steam_playtime_hours",
        "bm_playtime",
        "get_bm_playtime_hours",
        "created_at",
        "updated_at",
    ]

    readonly_fields = ["id", "created_at", "updated_at", "get_steam_playtime_hours", "get_bm_playtime_hours"]

    list_display = [
        "id",
        "steam_id",
        "game_id",
        "get_steam_playtime_hours",
        "get_bm_playtime_hours",
        "created_at",
        "updated_at",
    ]
    list_display_links = list_display
    search_fields = ["steam_id", "game_id"]
    list_filter = ["created_at", "updated_at"]
    sortable_by = ["id", "game_id", "created_at", "updated_at", "get_steam_playtime_hours", "get_bm_playtime_hours"]

    @admin.display(description="Игровое время по Steam (часы)")
    def get_steam_playtime_hours(self, obj):
        return int(obj.steam_playtime / 60 / 60) if obj.steam_playtime else None

    get_steam_playtime_hours.admin_order_field = "-steam_playtime"

    @admin.display(description="Игровое время по BM (часы)")
    def get_bm_playtime_hours(self, obj):
        return int(obj.bm_playtime / 60 / 60) if obj.bm_playtime else None

    get_bm_playtime_hours.admin_order_field = "-bm_playtime"


@admin.register(BattlemetricsSetPath)
class BattlemetricsSetPathAdmin(admin.ModelAdmin):
    list_display = ["change_button", "enabled", "path"]
    list_editable = ["enabled"]
    list_display_links = ["change_button", "path"]

    @admin.display(description="ID", ordering="id")
    def change_button(self, obj):
        return f"Изменить '{obj.id}'"


@admin.register(PlaytimeGetPath)
class PlaytimeGetPathAdmin(admin.ModelAdmin):
    list_display = ["change_button", "enabled", "path"]
    list_editable = ["enabled"]
    list_display_links = ["change_button", "path"]

    @admin.display(description="ID", ordering="id")
    def change_button(self, obj):
        return f"Изменить '{obj.id}'"
