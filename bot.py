# Главный файл Telegram-бота
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler,
)
 
from config import TELEGRAM_TOKEN
import api
import scraper
from logger import log
 
# Отключаем шумные логи httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
 
# Состояния диалога
(STATE_MAIN, STATE_SEARCH, STATE_TOP,
 STATE_STREAMER, STATE_CLIPS) = range(5)
 
# Клавиатура главного меню 
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🔍 Поиск игры"),   KeyboardButton("🏆 Топ игр")],
        [KeyboardButton("🟢 Стример"),      KeyboardButton("🎬 Клипы")],
        [KeyboardButton("📰 Новости игр")],
    ],
    resize_keyboard=True,
)
 
 
# /start
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    log(uid, "/start", f"User {name} started the bot")
    await update.message.reply_text(
        f"👾 Привет, {name}! Я Gaming Bot.\n"
        "Выбери действие на клавиатуре ниже:",
        reply_markup=MAIN_KEYBOARD,
    )
    return STATE_MAIN
 
 
# Обработка кнопок главного меню
async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    log(uid, f"Кнопка: {text}")
 
    prompts = {
        "🔍 Поиск игры":  ("Введи название игры:", STATE_SEARCH),
        "🏆 Топ игр":     ("Введи платформу (например, PS5 / Xbox / PC):", STATE_TOP),
        "🟢 Стример":     ("Введи логин стримера на Twitch:", STATE_STREAMER),
        "🎬 Клипы":       ("Введи название игры для поиска клипов:", STATE_CLIPS),
    }
 
    if text == "📰 Новости игр":
        await update.message.reply_text("🔍 Ищу свежие новости…")
        result = scraper.gaming_news()
        log(uid, "Новости игр (scraping)", result[:200])
        await update.message.reply_text(result, parse_mode="Markdown",
                                        reply_markup=MAIN_KEYBOARD)
        return STATE_MAIN
 
    if text in prompts:
        prompt, next_state = prompts[text]
        await update.message.reply_text(prompt)
        return next_state
 
    await update.message.reply_text("Используй кнопки меню.", reply_markup=MAIN_KEYBOARD)
    return STATE_MAIN
 
 
# Универсальный обработчик ввода пользователя
async def handle_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    state = ctx.user_data.get("__state__", STATE_MAIN)
 
    state_map = {
        STATE_SEARCH:   ("Поиск игры",  api.search_game),
        STATE_TOP:      ("Топ игр",     api.top_games),
        STATE_STREAMER: ("Стример",     api.streamer_status),
        STATE_CLIPS:    ("Клипы",       api.game_clips),
    }
 
    if state not in state_map:
        return await menu_handler(update, ctx)
 
    action_name, func = state_map[state]
    log(uid, f"{action_name} — запрос: {text}")
    await update.message.reply_text("⏳ Загружаю…")
 
    try:
        result = func(text)
    except Exception as e:
        result = f"Ошибка: {e}"
 
    log(uid, f"{action_name} — результат", result[:300])
    await update.message.reply_text(
        result,
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
        disable_web_page_preview=True,
    )
    return STATE_MAIN
 
 
def _make_state_setter(state):
    async def setter(update, ctx):
        ctx.user_data["__state__"] = state
        return await handle_input(update, ctx)
    return setter
 
 
# Запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
 
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_MAIN:     [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            STATE_SEARCH:   [MessageHandler(filters.TEXT & ~filters.COMMAND, _make_state_setter(STATE_SEARCH))],
            STATE_TOP:      [MessageHandler(filters.TEXT & ~filters.COMMAND, _make_state_setter(STATE_TOP))],
            STATE_STREAMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, _make_state_setter(STATE_STREAMER))],
            STATE_CLIPS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, _make_state_setter(STATE_CLIPS))],
        },
        fallbacks=[CommandHandler("start", start)],
    )
 
    app.add_handler(conv)
    print("✅ Бот запущен!")
    app.run_polling()
 
 
if __name__ == "__main__":
    main()