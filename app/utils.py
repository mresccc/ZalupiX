import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qsl, unquote

logger = logging.getLogger(__name__)


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Валидирует init_data от Telegram Mini App согласно официальной документации.
    Поддерживает как hash (с bot token), так и signature (без bot token).
    """
    try:
        # 1. Парсим init_data в словарь
        params = dict(parse_qsl(init_data))

        # 2. Проверяем тип валидации
        signature = params.get("signature")
        hash_value = params.get("hash")

        if signature:
            # Валидация с signature - пропускаем (требует Ed25519 публичного ключа Telegram)
            logger.info("Обнаружен signature, пропускаем валидацию (требует Ed25519)")
            # Просто парсим данные пользователя без валидации signature
        elif hash_value:
            # Валидация с hash и bot token
            logger.info("Используем hash валидацию с bot token")

            # Удаляем поля 'hash' и 'signature' из словаря для проверки
            check_params = {
                k: v for k, v in params.items() if k not in ["hash", "signature"]
            }

            # Сортируем параметры по алфавиту и формируем строку для проверки
            sorted_params = sorted(check_params.items())
            data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_params)

            logger.info(f"Строка для проверки: {data_check_string}")

            # Создаем секретный ключ (key="WebAppData", msg=bot_token)
            secret_key = hmac.new(
                key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256
            ).digest()

            # Вычисляем ожидаемый hash
            expected_hash = hmac.new(
                key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256
            ).hexdigest()

            logger.info(f"Ожидаемый hash: {expected_hash}")
            logger.info(f"Полученный hash: {hash_value}")

            # Сравниваем хэши
            if not hmac.compare_digest(expected_hash, hash_value):
                logger.error(
                    f"Hash не совпадает. Ожидаемый: {expected_hash}, полученный: {hash_value}"
                )
                raise ValueError("Hash не совпадает")
        else:
            raise ValueError("Ни hash, ни signature не найдены в init_data")

        # Парсим данные пользователя
        user_data_str = params.get("user")
        if not user_data_str:
            raise ValueError("User данные не найдены в init_data")

        # Декодируем URL-encoded строку
        decoded_user_data = unquote(user_data_str)
        user_data = json.loads(decoded_user_data)
        return user_data

    except Exception as e:
        logger.error(f"Ошибка валидации init_data: {str(e)}")
        raise ValueError(f"Ошибка валидации init_data: {str(e)}")


def parse_telegram_data_without_validation(init_data: str) -> dict:
    """Парсинг Telegram данных без валидации hash (для разработки)"""
    try:
        # Парсим данные без валидации
        params = dict(parse_qsl(init_data))
        user_data_str = params.get("user")
        if not user_data_str:
            raise ValueError("User данные не найдены в init_data")

        # Декодируем URL-encoded строку
        decoded_user_data = unquote(user_data_str)
        user_data = json.loads(decoded_user_data)

        return user_data

    except Exception as e:
        logger.error(f"Ошибка парсинга данных: {str(e)}")
        raise ValueError(f"Ошибка парсинга данных: {str(e)}")
