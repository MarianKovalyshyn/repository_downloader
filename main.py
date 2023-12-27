import logging
import os

from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I can help you to download GitHub repository.\n"
        "Type /downloadrepo to start.",
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Send /cancel to end operation.\n" "Enter user's login:",
    )

    return 1


async def project_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    print(update.message.text)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter project name:",
    )

    return 2


async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.message.text)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Done. Have a nice day!",
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Have a nice day!"
    )

    return ConversationHandler.END


if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    download_repo_handler = ConversationHandler(
        entry_points=[CommandHandler("downloadrepo", login)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, project_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, goodbye)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(download_repo_handler)

    application.run_polling()
