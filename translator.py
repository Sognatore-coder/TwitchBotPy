# Перевод текста на русский
from deep_translator import GoogleTranslator


def translate(text: str, max_chars: int = 4500) -> str:
    if not text or not text.strip():
        return text
    try:
        chunk = text[:max_chars]
        result = GoogleTranslator(source="auto", target="ru").translate(chunk)
        return result or text
    except Exception:
        # При ошибке перевода возвращаем оригинал
        return text
