
import os
import asyncio
import logging
from collections import defaultdict, deque

from google import genai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Maxfiy kalitlar GitHub Secrets ichidan olinadi
BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Gemini AI
ai = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-flash-latest"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Har bir foydalanuvchining oxirgi suhbat xabarlari
# Bot qayta ishga tushsa, bu vaqtinchalik xotira tozalanadi.
history = defaultdict(lambda: deque(maxlen=12))

SYSTEM_PROMPT = """
Sen foydali, aqlli va xushmuomala o'zbek tilida
gaplasha oladigan AI yordamchisan.
Foydalanuvchining savollariga aniq va tushunarli javob ber.
Savol boshqa tilda bo'lsa, o'sha tilda ham javob bera ol.
Bilmagan narsangni to'qib chiqarma.
Kerak bo'lsa, javobni bosqichma-bosqich tushuntir.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Salom! Men AI yordamchiman 🤖\n\n"
        "Menga istalgan savolingni yoz.\n"
        "Yangi suhbat boshlash uchun /reset buyrug'ini yubor."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history.pop(user_id, None)
    await update.effective_message.reply_text(
        "Suhbat xotirasi tozalandi. Yangi savolingni yoz!"
    )


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user or not message.text:
        return

    question = message.text.strip()

    if not question:
        return

    if len(question) > 12000:
        await message.reply_text(
            "Savoling juda uzun. Iltimos, qisqartirib yubor."
        )
        return

    status = await message.reply_text("🤔 Javob tayyorlayapman...")

    try:
        conversation = [
            {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT}],
            },
            {
                "role": "model",
                "parts": [{"text": "Tushundim. Savollarga yordam beraman."}],
            },
        ]

        conversation.extend(list(history[user.id]))
        conversation.append({
            "role": "user",
            "parts": [{"text": question}],
        })

        response = await asyncio.to_thread(
            ai.models.generate_content,
            model=MODEL,
            contents=conversation,
        )

        result = response.text

        if not result:
            result = "Kechirasan, bu safar javob tayyorlay olmadim."

        history[user.id].append({
            "role": "user",
            "parts": [{"text": question}],
        })
        history[user.id].append({
            "role": "model",
            "parts": [{"text": result[:12000]}],
        })

        # Telegram xabar uzunligi cheklangan.
        for start_index in range(0, len(result), 4000):
            await message.reply_text(result[start_index:start_index + 4000])

        await status.delete()

    except Exception:
        logger.exception("AI javobida xato")
        await status.edit_text(
            "Javob olishda xatolik yuz berdi. "
            "Birozdan keyin qayta urinib ko'r."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, answer)
    )

    logger.info("AI Telegram bot ishga tushmoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()
