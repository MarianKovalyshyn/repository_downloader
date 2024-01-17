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

LOGIN, PROJECT_NAME = range(2)

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
    context.user_data["username"] = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter *project name*:",
        parse_mode="Markdown",
    )

    return PROJECT_NAME


async def project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base_url = "https://api.github.com/repos/"
    end_url = "zipball/"
    repo_name = update.message.text
    username = context.user_data["username"]
    final_url = base_url + username + "/" + repo_name + "/" + end_url
    file_name = f"{repo_name}[{username}]({date.today()}).zip"
    project_to_send, file_status = prepare_project_to_send(
        repository_name=repo_name,
        repository_url=final_url,
        username=username,
        file_name=file_name,
    )

    if project_to_send:
        log_action(repo_name, username, file_status)
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(project_to_send, "rb"),
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Done. Have a nice day!",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="User or repository not found. Try again.",
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Have a nice day!"
    )

    return ConversationHandler.END


def find_cached_project(repository_name: str, username: str) -> str | None:
    local_project = glob.glob(f"{repository_name}[[]{username}[]]*.zip")
    return local_project[0] if local_project else None


def download_project(file_name, project_url: str) -> str:
    response = requests.get(project_url)
    if response.status_code == 404:
        return ""
    else:
        open(file_name, "wb").write(response.content)
    return file_name


def extract_project_date(project_to_send: str) -> date:
    local_project_date = project_to_send[
        project_to_send.find("(") + 1: project_to_send.find(")")
    ]
    local_project_date_object = datetime.strptime(
        local_project_date, "%Y-%m-%d"
    ).date()

    return local_project_date_object


def update_project_if_needed(
    project_to_send: str, project_date: date, file_name: str, final_url: str
) -> (str, str):
    file_status = "cached"

    if (date.today() - project_date).days > 7:
        file_status = "updated"
        os.remove(project_to_send)
        project_to_send = download_project(file_name, final_url)

    return project_to_send, file_status


def prepare_project_to_send(
    repository_name: str,
    repository_url: str,
    username: str,
    file_name: str = None,
) -> (str, str):
    project_to_send = find_cached_project(repository_name, username)

    if not project_to_send:
        file_status = "downloaded"
        project_to_send = download_project(file_name, repository_url)
    else:
        project_date = extract_project_date(project_to_send)
        project_to_send, file_status = update_project_if_needed(
            project_to_send=project_to_send,
            project_date=project_date,
            file_name=file_name,
            final_url=repository_url,
        )

    return project_to_send, file_status


def log_action(repository_name: str, username: str, file_status: str) -> None:
    with open("logs.txt", "a") as file:
        file.write(
            f"Project {repository_name} from {username}`s repository was send "
            f"on {datetime.now()} ({file_status})\n"
        )


if __name__ == "__main__":
    load_dotenv()
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
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    application.add_handler(start_handler)
    application.add_handler(download_repo_handler)
    application.run_polling()

# TODO add tests
# TODO add info to README
