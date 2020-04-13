# thornode-telegram-bot ⚡🤖
A telegram bot to monitor the status of THORNodes.

## Requirements
* Python3
* Telegram
* Docker (if you want to run as docker container)

## Steps to run
* Install dependencies
* Create Telegram bot token via [BotFather](https://t.me/BotFather)
* Set Telegram token as environment variable
* Start the mock THORNode endpoint
* Start the bot
* Run & test the bot
* Production

## Install dependencies
Install all required libraries via `pip install -r requirements.txt`.

## Create Telegram bot token via BotFather
Start a Telegram chat with [BotFather](https://t.me/BotFather) and click `start`.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token. Save this token in a secure location (for example in an environment variable ;).

## Set Telegram token as environment variable
Save the above created telegram token in the environment variable `TELEGRAM_BOT_TOKEN`.

To do this, in your terminal type `export TELEGRAM_BOT_TOKEN=XXX`, where the value after the `=` should be your own bot token.

Alternatively, if your using a Jetbrains IDE, like Pycharm, you can set this environment variable for your run configuration, which is very convenient for development (https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm).

## Start the mock THORNode endpoint
To test whether the bot actually notifies us about changes we need a way to manipulate the data the bot is fetching.

Do that with the local json file `nodeaccounts.json`.

Go to the directory of this repo in your terminal, and start a local server with:

```
python3 -m http.server 8000 --bind 127.0.0.1 -d test
```

If everything works, this local endpoint returns you the content of `nodeaccounts.json`:
```
http://localhost:8000/nodeaccounts.json
```

## Start the bot
Open the directory in your terminal, and start the bot via
```
python3 thornode_bot.py
```

Make sure to see a message in the console that the bot is running.

## Run & test the bot
When you created the telegram token via BotFather, you gave your bot a specific name. Now search for this name in your Telegram client, open the chat and hit start!

At this point, you can play with the bot, see what it does and assert that it does the right thing!

This bot is persistent, which means, it stores data in the file `storage/session.data`.  Once you stop and restart the bot again, everything should continue as if the bot was never stopped (because of the persisting the session data).

If you don't want the bot to be persistent, simply delete the file `session.data` in the `storage` folder before startup.

## Production
In production we do not use data from our local mock THORNode endpoint but real network data.
