# thornode-telegram-bot ⚡🤖
A telegram bot to monitor the status of THORNodes.

## Requirements
* Telegram
* Docker (if you want to run with docker)
* Python3 (if you want to run without docker)

## Quickstart

Install `docker` and run:

```
docker volume create thornode-bot-volume
docker run --env TELEGRAM_BOT_TOKEN=XXX --env DEBUG={True|False} --mount source=thornode-bot-volume,target=/storage block42blockchaincompany/thornode_bot
```

Make sure to set the correct values for `TELEGRAM_BOT_TOKEN` and `DEBUG`.

## Steps to run everything yourself
* Install dependencies
* Create Telegram bot token via [BotFather](https://t.me/BotFather)
* Set environment variables
* Start the mock THORNode endpoint
* Start the bot
* Run & test the bot
* Production

## Install dependencies
Install all required dependencies via: `pip install -r requirements.txt`

## Create Telegram bot token via BotFather
Start a Telegram chat with [BotFather](https://t.me/BotFather) and click `start`.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token. Save this token, you will need it in a second.

## Set environment variables
Set the telegram bot token you just created as an environment variable: `TELEGRAM_BOT_TOKEN`

```
export TELEGRAM_BOT_TOKEN=XXX
```

If your using a Jetbrains IDE (e.g. Pycharm), you can set this environment variable for your run configuration which is very convenient for development (see: https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm).

## Start the mock THORNode endpoint
To test whether the bot actually notifies you about changes, the data the bot is quering needs to change. You can simulate that by manually editing `test/nodeaccounts.json`.

Go to the root directory of this project and start the mock endpoint (`-d` specifies the webroot where we use the `test` directory):

```
python3 -m http.server 8000 --bind 127.0.0.1 -d test
```

If everything works fine you should receive the content of `test/nodeaccounts.json` at this endpoint:

```
http://localhost:8000/nodeaccounts.json
```

## Start the bot
Start the bot via:

```
python3 thornode_bot.py
```

Make sure to see a message in the console that the bot is running.

## Run & test the bot
When you created the telegram bot token via BotFather, you gave your bot a certain name (e.g. `thornode_bot`). Now search for this name in Telegram, open the chat and hit start!

At this point, you can play with the bot, see what it does and check that everything works fine!

The bot persistents all data, which means it stores its chat data in the file `storage/session.data`.  Once you stop and restart the bot, everything should continue as if the bot was never stopped.

If you want to reset your bot's data, simply delete the file `session.data` in the `storage` directory before startup.

## Production
In production you do not want to use mock data from the local endpoint but real network data. To get real data just set `DEBUG=False` in your environment variables and the bot will use available seed nodes for data retrieval.

### Docker
To run the bot as a docker container, make sure you have docker installed (see: https://docs.docker.com/get-docker).

Navigate to the root directory of this reposiroty and execute the following commands:

Build the docker image as described in the `Dockerfile`:

```
docker build -t thornode-bot .
```

To make the bot's data persistent, you need to create a docker volume. If the bot crashes or restarts the volume won't be affected and keeps all the session data:

```
docker volume create thornode-bot-volume
```

Finally run the docker container:

```
docker run --env TELEGRAM_BOT_TOKEN=XXX --mount source=thornode-bot-volume,target=/storage thornode-bot
```

Replace the `--env` flag with your telegram bot token. Finally, the `--mount` flag tells docker to mount our previously created volume in the directory `storage`. This is the directory where your bot saves and retrieves the `session.data` file.
