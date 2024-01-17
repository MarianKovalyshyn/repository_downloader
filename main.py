import logging
import os
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

from tools import prepare_project_to_send, log_action

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
