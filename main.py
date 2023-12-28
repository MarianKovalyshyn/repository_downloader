import logging
import os
import requests
from datetime import date

from dotenv import load_dotenv
from telegram import Update
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
LOGIN, PROJECT_NAME = range(2)
BASE_URL = "https://api.github.com/repos/"
END_URL = "zipball/"
FINAL_URL = ""

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


async def download_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Send /cancel to end operation.\n" "Enter user's login:",
    )

    return LOGIN


async def login(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    global FINAL_URL
    FINAL_URL += BASE_URL + update.message.text + "/"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter project name:",
    )

    return PROJECT_NAME


async def project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FINAL_URL
    FINAL_URL += update.message.text + "/" + END_URL

    file_name = f"{update.message.text}({date.today()}).zip"
    open(file_name, "wb").write(requests.get(FINAL_URL).content)
    FINAL_URL = ""

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
        entry_points=[CommandHandler("downloadrepo", download_repo)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)],
            PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, project_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(download_repo_handler)

    application.run_polling()
