import hmac
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from dateutil.parser import isoparse as datetime_isoparse
from rest_framework.request import Request
from rest_framework.validators import ValidationError


class BaseRequestHMACValidator(ABC):
    """
    Абстрактный класс валидатора HMAC в запросе
    """

    def __init__(self, *, header: str, signature_regex: str, secret_key: str, hash_type: str) -> None:
        self.header = header
        self.signature_regex = signature_regex
        self.secret_key = secret_key
        self.hash_type = hash_type

    @abstractmethod
    def validate_hmac(self, *, request: Request) -> None:
        """Получает сигнатуры из заголовка запроса, генерирует сигнатуру из
        данных и проверяет их вместе

        Raises:
            ValidationError: В любой непонятной ситуации
        """
        raise NotImplementedError("validate_hmac is not implemented")

    @abstractmethod
    def _get_signature_from_request(self, *, request: Request) -> str | None:
        """Получает сигнатуру по регулярке из заголовка полученного запроса

        Raises:
            ValidationError: Если сигнатуру получить не удалось
        Returns:
            str: Сигнатура
        """
        raise NotImplementedError("get_signature_from_request is not implemented")

    @abstractmethod
    def _generate_signature_from_request(self, *, request: Request) -> str:
        """Генерирует сигнатуру через hmac.digest из данных самого запроса

        Raises:
            ValidationError: Если по каким то причинам генерация сигнатуры
                             невозможна
        Returns:
            str: Сигнатура
        """
        raise NotImplementedError("generate_signature_from_request is not implemented")

    def _compare_signature(self, sign_1, sign_2) -> bool:
        """Сравнивает две сигнатура через функцию с постоянным временем

        Args:
            sign_1 (str): Сигнатура 1
            sign_2 (str): Сигнатура 2

        Returns:
            bool: True если сигнатуры одинаковые, False если разные
        """
        return hmac.compare_digest(sign_1, sign_2)


class DefaultRequestHMACValidator(BaseRequestHMACValidator):
    """
    Стандартный валидатор HMAC, получает сигнатуру из заголовка по регулярке
    без какой либо логики, во время локальный генерации из hmac из данных
    запроса - просто передаёт request.data в hmac.digest, тоже без особой
    логики
    """

    def validate_hmac(self, *, request: Request) -> None:
        if self.header not in request.headers:
            raise ValidationError("HMAC header not found")

        signature_from_request = self._get_signature_from_request(request=request)

        if signature_from_request is None:
            raise ValidationError("HMAC signature in header not found")

        generated_signature: str = self._generate_signature_from_request(request=request)

        if not self._compare_signature(signature_from_request, generated_signature):
            raise ValidationError("Request body, signature or secret key is corrupted, hmac does not match")

    def _get_signature_from_request(self, *, request: Request) -> str | None:
        header = request.headers[self.header]

        match_header: re.Match | None = re.search(
            self.signature_regex,
            header,
            re.A,
        )
        return match_header.group(0) if match_header else None

    def _generate_signature_from_request(self, *, request: Request) -> str:
        return hmac.digest(
            self.secret_key.encode(),
            request.body,
            self.hash_type,
        ).hex()


class TimestampRequestHMACValidator(DefaultRequestHMACValidator):
    r"""Валидатор запроса по hmac для запросов от сервисов которые добавляют в HMAC заголовок timestamp,
    например Battlemetrics

    Формат заголовка:
    t=ISO_DATETIME,s=DATA

    ISO_DATETIME должен быть с часовым поясом

    Пример hmac_signature_regex для Battlemetrics - (?<=s=)\w+(?=,|\Z)
    Пример hmac_timestamp_regex для Battlemetrics - (?<=t=)[\w\-:.+]+(?=,|\Z)

    Разница в том, что Battlemetrics передаёт в заголовке сигнатуры еще
    и timestamp в iso формате, данный валидатор ищет эту дату, парсит и
    сравнивает текущее время с временем timestamp (с учетом возможного
    отклонения его от текущего времени в одну и в другую сторону)

    Сигнатура из request.data формируется из данных в формате
    {timestamp}.{request.data}
    """

    def __init__(
        self,
        *,
        header: str,
        signature_regex: str,
        timestamp_regex: str,
        timestamp_deviation: int,
        secret_key: str,
        hash_type: str,
    ) -> None:
        super().__init__(header=header, signature_regex=signature_regex, secret_key=secret_key, hash_type=hash_type)

        self.hmac_timestamp_regex = timestamp_regex
        self.hmac_timestamp_deviation: timedelta = timedelta(abs(timestamp_deviation))

    def _generate_signature_from_request(self, *, request: Request) -> str:
        now: datetime = datetime.now(timezone.utc)
        header = request.headers[self.header]

        timestamp_match = re.search(self.hmac_timestamp_regex, header, flags=re.A)

        if timestamp_match is None:
            raise ValidationError("Timestamp in HMAC header not found")

        timestamp_text = timestamp_match.group(0)

        try:
            timestamp = datetime_isoparse(timestamp_text)
        except ValueError:
            raise ValidationError("Timestamp in HMAC header have not valid format, required iso format")

        if timestamp.tzinfo is None:
            raise ValidationError("Timestamp in HMAC header must have a timezone")

        if not (now - self.hmac_timestamp_deviation < timestamp < now + self.hmac_timestamp_deviation):
            raise ValidationError("Timestamp is very old or very far in the future")

        return hmac.digest(
            self.secret_key.encode(),
            f"{timestamp_text}.".encode() + request.body,
            self.hash_type,
        ).hex()
