import logging
import os
import glob
import requests
from datetime import date, datetime

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
USERNAME = ""
REPO_NAME = ""

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
        text="Send /cancel to cancel operation.\nEnter user's login:",
    )

    return LOGIN


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global FINAL_URL, USERNAME
    USERNAME = update.message.text
    FINAL_URL += BASE_URL + USERNAME + "/"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter project name:",
    )

    return PROJECT_NAME


async def project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FINAL_URL, REPO_NAME
    REPO_NAME = update.message.text
    FINAL_URL += REPO_NAME + "/" + END_URL
    local_projects = [project for project in glob.glob(f"{REPO_NAME}*.zip")]
    project_to_use = ""

    for project in local_projects:
        if f"[{USERNAME}]" in project:
            project_to_use = project
            break

    file_name = f"{REPO_NAME}[{USERNAME}]({date.today()}).zip"
    used_cached_file = True

    if not project_to_use:
        open(file_name, "wb").write(requests.get(FINAL_URL).content)
        project_to_use = file_name
        used_cached_file = False
    else:
        local_project_date = project_to_use[
            project_to_use.find("(") + 1: project_to_use.find(")")
        ]
        local_project_date_object = datetime.strptime(local_project_date, "%Y-%m-%d").date()

        if (date.today() - local_project_date_object).days > 7:
            os.remove(project_to_use)
            open(file_name, "wb").write(requests.get(FINAL_URL).content)
            project_to_use = file_name
            used_cached_file = False

    with open("logs.txt", "a") as file:
        cached_or_downloaded = "cached" if used_cached_file else "downloaded"
        file.write(f"Project {REPO_NAME} from {USERNAME}`s repository was send "
                   f"on {date.today()} ({cached_or_downloaded})\n")

    FINAL_URL = ""
    await context.bot.send_document(
        chat_id=update.effective_chat.id, document=open(project_to_use, "rb")
    )
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
            PROJECT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, project_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(download_repo_handler)
    application.run_polling()

# TODO 1) divide code into functions
