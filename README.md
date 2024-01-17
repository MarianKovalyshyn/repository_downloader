# Repository Downloader Bot
This is a Telegram Bot for downloading zip files from GitHub repository.
If file is older than 7 days or there is no such file yet, 
there will be request to repository and file will be downloaded/updated.

## Features
* You can download zip archive of repository using Telegram Bot
* All action are logged in logs.txt file

## Installing using GitHub
Install PostgreSQL and create a database.

```shell
git clone https://github.com/MarianKovalyshyn/repository_downloader.git
cd repository_downloader/
python -m venv venv
source venv/bin/activate (MacOS)
venv\Scripts\activate (Windows)
pip install -r requirements.txt
python main.py
```

## Example of usage
![img.png](img.png)
