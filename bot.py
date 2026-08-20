import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ربات با موفقیت روشن شد!")


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        print("❌ BOT_TOKEN تنظیم نشده است.")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    print("✅ ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
