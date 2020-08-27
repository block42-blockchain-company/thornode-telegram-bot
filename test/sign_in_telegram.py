import os

from pyrogram import Client as TelegramClient

telegram = TelegramClient(
    ":memory:",
    api_id=os.environ['TELEGRAM_API_ID'],
    api_hash=os.environ['TELEGRAM_API_HASH']
)

with telegram:
    print("Successfully logged in!")
    print("Session string: ")

    session_string = telegram.export_session_string()
    print(session_string)

    with open('telegram_session.string', 'w') as write_file:
        write_file.write(session_string)
