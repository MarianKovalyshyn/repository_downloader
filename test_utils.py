from datetime import date
from unittest.mock import patch, mock_open
from utils import (
    find_cached_project,
    download_project,
    extract_project_date,
    update_project_if_needed,
    log_action,
)


def test_find_cached_project_returns_project_when_exists():
    with patch("utils.glob.glob", return_value=["project"]) as mock_glob:
        result = find_cached_project("project_id", "username")
        assert result == "project"
        mock_glob.assert_called_once_with("project_id[[]username[]]*.zip")


def test_find_cached_project_returns_none_when_not_exists():
    with patch("utils.glob.glob", return_value=[]) as mock_glob:
        result = find_cached_project("project_id", "username")
        assert result is None
        mock_glob.assert_called_once_with("project_id[[]username[]]*.zip")


def test_download_project_successfully():
    with patch("utils.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"content"
        with patch(
            "builtins.open", new_callable=mock_open()
        ) as mock_open_file:
            result = download_project("file_name", "project_url")
            assert result == "file_name"
            mock_get.assert_called_once_with("project_url")
            mock_open_file.assert_called_once_with("file_name", "wb")


def test_download_project_returns_empty_string_when_not_found():
    with patch("utils.requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        result = download_project("file_name", "project_url")
        assert result == ""
        mock_get.assert_called_once_with("project_url")


def test_extract_project_date_returns_correct_date():
    result = extract_project_date("project(2022-01-01)")
    assert result == date(2022, 1, 1)


def test_update_project_if_needed_when_update_needed():
    with patch("utils.os.remove") as mock_remove:
        with patch(
            "utils.download_project", return_value="new_project"
        ) as mock_download:
            result, status = update_project_if_needed(
                "project", date(2022, 1, 1), "file_name", "final_url"
            )
            assert result == "new_project"
            assert status == "updated"
            mock_remove.assert_called_once_with("project")
            mock_download.assert_called_once_with("file_name", "final_url")


def test_update_project_if_needed_when_no_update_needed():
    result, status = update_project_if_needed(
        "project", date.today(), "file_name", "final_url"
    )
    assert result == "project"
    assert status == "cached"


def test_log_action_logs_correctly():
    with patch("builtins.open", new_callable=mock_open()) as mock_open_file:
        log_action("repository_name", "username", "file_status")
        mock_open_file.assert_called_once_with("logs.txt", "a")
