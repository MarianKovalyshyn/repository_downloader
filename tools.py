import os
import glob
from datetime import date, datetime

import requests


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
