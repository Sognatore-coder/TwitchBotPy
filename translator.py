# translator.py — перевод текста на русский через deep-translator
from deep_translator import GoogleTranslator


def translate(text: str, max_chars: int = 4500) -> str:
    """Переводит текст на русский. Если уже на русском — возвращает как есть."""
    if not text or not text.strip():
        return text
    try:
        # GoogleTranslator имеет лимит ~5000 символов на запрос
        chunk = text[:max_chars]
        result = GoogleTranslator(source="auto", target="ru").translate(chunk)
        return result or text
    except Exception:
        # При ошибке перевода возвращаем оригинал
        return text
