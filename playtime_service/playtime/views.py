from typing import Any

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BattlemetricsSetPath, PlaytimeGetPath
from .request_validators import (
    DefaultRequestHMACValidator,
    TimestampRequestHMACValidator,
)
from .services import (
    get_playtimes_with_search_unknown,
    get_playtimes_with_update,
    update_or_create_playtime,
)


class BattleMetricsPlaytimeUpdateApi(APIView):
    class InputSerializer(serializers.Serializer):
        steam_id = serializers.RegexField(r"^76\d{15,16}$")
        playtime = serializers.IntegerField()
        game_id = serializers.IntegerField(min_value=0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.serializer_class = self.InputSerializer

    def post(self, request, path) -> Response:
        battlemetrics_path = get_object_or_404(BattlemetricsSetPath, path=path)

        if not battlemetrics_path.enabled:
            return Response(status=status.HTTP_403_FORBIDDEN)

        validator = TimestampRequestHMACValidator(
            header="X-Signature",
            hash_type="sha256",
            secret_key=battlemetrics_path.hmac_secret_key,
            signature_regex=settings.BATTLEMETRICS_SIGNATURE_REGEX,
            timestamp_regex=settings.BATTLEMETRICS_TIMESTAMP_REGEX,
            timestamp_deviation=settings.HMAC_TIMESTAMP_DEVIATION,
        )

        if settings.ENABLE_HMAC_VALIDATION:
            validator.validate_hmac(request=request)

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_or_create_playtime(
            steam_id=serializer.validated_data["steam_id"],  # type: ignore
            game_id=serializer.validated_data["game_id"],  # type: ignore
            bm_playtime=serializer.validated_data["playtime"],  # type: ignore
        )

        return Response(status=status.HTTP_200_OK)


class PlaytimeGetApi(APIView):
    class InputSerializer(serializers.Serializer):
        steam_ids = serializers.ListField(
            child=serializers.RegexField(r"^76\d{15,16}$"), allow_empty=False, max_length=120
        )
        game_id = serializers.IntegerField()
        is_need_update = serializers.BooleanField(default=False)

    class OutputSerializer(serializers.Serializer):
        steam_id = serializers.CharField()
        steam_playtime = serializers.IntegerField()
        bm_playtime = serializers.IntegerField()
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.serializer_class = self.InputSerializer

    def post(self, request, path):
        playtime_path = get_object_or_404(PlaytimeGetPath, path=path)

        if not playtime_path.enabled:
            return Response(status=status.HTTP_403_FORBIDDEN)

        validator = DefaultRequestHMACValidator(
            header="X-Signature", hash_type="sha256", secret_key=playtime_path.hmac_secret_key, signature_regex=".*"
        )

        if settings.ENABLE_HMAC_VALIDATION:
            validator.validate_hmac(request=request)

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["is_need_update"]:  # type: ignore
            playtimes = get_playtimes_with_update(
                steam_ids=serializer.validated_data["steam_ids"],  # type: ignore
                game_id=serializer.validated_data["game_id"],  # type: ignore
            )
        else:
            playtimes = get_playtimes_with_search_unknown(
                steam_ids=serializer.validated_data["steam_ids"],  # type: ignore
                game_id=serializer.validated_data["game_id"],  # type: ignore
            )

        return Response(self.OutputSerializer(playtimes, many=True).data)
