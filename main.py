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
        text="Send /cancel to cancel this operation.\nEnter user's *login*:",
        parse_mode="Markdown",
    )

    return LOGIN


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global FINAL_URL, USERNAME
    USERNAME = update.message.text
    FINAL_URL += BASE_URL + USERNAME + "/"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter *project name*:",
        parse_mode="Markdown",
    )

    return PROJECT_NAME


def find_cached_project(repository_name: str, username: str) -> str | None:
    local_project = glob.glob(f"{repository_name}[[]{username}[]]*.zip")
    return local_project[0] if local_project else None


def download_project(file_name, project_url: str) -> (str, bool):
    open(file_name, "wb").write(requests.get(project_url).content)
    return file_name, False


def extract_project_date(project_to_send: str) -> date:
    local_project_date = project_to_send[
        project_to_send.find("(") + 1: project_to_send.find(")")
    ]
    local_project_date_object = datetime.strptime(
        local_project_date, "%Y-%m-%d"
    ).date()

    return local_project_date_object


def update_project_if_needed(
    project_to_send: str, project_date: date, file_name: str
):
    if (date.today() - project_date).days > 7:
        os.remove(project_to_send)
        project_to_send, used_cached_file = download_project(
            file_name, FINAL_URL
        )
        return project_to_send, used_cached_file


def prepare_project_to_send(
    repository_name: str,
    repository_url: str,
    username: str,
    file_name: str = None,
) -> (str, bool):
    project_to_send = find_cached_project(repository_name, username)

    if not project_to_send:
        project_to_send, used_cached_file = download_project(
            file_name, repository_url
        )
    else:
        project_date = extract_project_date(project_to_send)
        project_to_send, used_cached_file = update_project_if_needed(
            project_to_send=project_to_send,
            project_date=project_date,
            file_name=file_name,
        )

    log_action(REPO_NAME, USERNAME, used_cached_file)

    return project_to_send


def log_action(
    repository_name: str, username: str, used_cached_file: bool = False
) -> None:
    with open("logs.txt", "a") as file:
        cached_or_downloaded = "cached" if used_cached_file else "downloaded"
        file.write(
            f"Project {repository_name} from {username}`s repository was send "
            f"on {datetime.now()} ({cached_or_downloaded})\n"
        )


async def project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FINAL_URL, REPO_NAME
    REPO_NAME = update.message.text
    FINAL_URL += REPO_NAME + "/" + END_URL
    file_name = f"{REPO_NAME}[{USERNAME}]({date.today()}).zip"
    project_to_send = prepare_project_to_send(
        repository_name=REPO_NAME,
        repository_url=FINAL_URL,
        username=USERNAME,
        file_name=file_name,
    )
    FINAL_URL = ""

    await context.bot.send_document(
        chat_id=update.effective_chat.id, document=open(project_to_send, "rb")
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
    start_handler = CommandHandler("start", start)
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
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(start_handler)
    application.add_handler(download_repo_handler)
    application.run_polling()
