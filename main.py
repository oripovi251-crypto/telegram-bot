import os
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]
TAQIQLANGAN = [
    "uyatsiz_soz",
    "uyatsiz_nik",
    "18plus",
]


async def tekshir_xabar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if user.is_bot:
        return

    member = await message.chat.get_member(user.id)

    if member.status in ["administrator", "creator"]:
        return

    username = (user.username or "").lower()
    first_name = (user.first_name or "").lower()
    last_name = (user.last_name or "").lower()
    text = (message.text or message.caption or "").lower()

    hammasi = f"{username} {first_name} {last_name} {text}"

    for taqiqlangan in TAQIQLANGAN:
        if taqiqlangan in hammasi:
            try:
                await message.delete()
            except Exception:
                pass

            try:
                await context.bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                )
            except Exception:
                pass

            return


async def yangi_azo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_update = update.chat_member

    if not member_update:
        return

    user = member_update.new_chat_member.user

    if user.is_bot:
        return

    username = (user.username or "").lower()
    first_name = (user.first_name or "").lower()
    last_name = (user.last_name or "").lower()

    hammasi = f"{username} {first_name} {last_name}"

    for taqiqlangan in TAQIQLANGAN:
        if taqiqlangan in hammasi:
            try:
                await context.bot.ban_chat_member(
                    chat_id=member_update.chat.id,
                    user_id=user.id,
                )
            except Exception:
                pass

            return


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.ALL,
            tekshir_xabar,
        )
    )

    app.add_handler(
        ChatMemberHandler(
            yangi_azo,
            ChatMemberHandler.CHAT_MEMBER,
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
