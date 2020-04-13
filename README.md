# thornode-telegram-bot ⚡🤖
A telegram bot to monitor the status of THORNodes.

## Requirements
* Python3
* Telegram Client

## Steps to run
* Install `python-telegram-bot` library
* Create Telegram bot token via [BotFather](https://t.me/BotFather)
* Set Telegram token as environment variable
* Start local THORNode endpoint
* Start the bot
* Run & test the bot
* Production
    - Docker

## Install python-telegram-bot library
In your terminal type `pip install python-telegram-bot`. Alternatively you can add the module in your IDE as described by the vendor.

## Create Telegram bot token via BotFather
Start a Telegram chat with [BotFather](https://t.me/BotFather) and click `start`.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token. Save this token in a secure location (for example in an environment variable ;).

## Set Telegram token as environment variable
Save the above created telegram token in the environment variable `TELEGRAM_BOT_TOKEN`.

To do this, in your terminal type `export TELEGRAM_BOT_TOKEN=1234567890:xxxYourTokenxxxxx`, where
the value after the `=` should be your own token.

Alternatively, if your using a Jetbrains IDE like Pycharm, you can set this environment variable
for your configuration, which is convenient for development (https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm).

## Start local THORNode endpoint
To test whether the bot actually notifies us about changes we need a way to manipulate the data the bot is fetching.

Do that with the local json file `node_data.json`.

Go to the directory of this repo in your terminal, and start a local server with:

```
python3 -m http.server 8000 --bind 127.0.0.1
```

If everything works, this local endpoint returns you the content of node_data.json:
```
http://localhost:8000/node_data.json
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
For production you use real THORNode data, not from the local python endpoint.

Comment out this line `return HARDCODED_LOCAL_NODE`. The return statement below returns the IP address to get values from the testnet.

### Docker
To run the bot as a docker container, you need to have docker installed 
(check out https://docs.docker.com/get-docker/ if you haven't).

Navigate to the directory of this repo, and execute the following commands.
The first command builds the docker image as described in the Dockerfile:
```
docker build -t thornode-telegram-alert-bot .
```
To make the bot persistent, we need to create a volume. If the bot crashes or is restarted, 
the volume won't be affected and keeps the session data:
```
docker volume create thorbot-session-data-vol
```
Then to run the docker image as a container, run:
```
docker run --env TELEGRAM_TOKEN=xxxxxYourTokenxxxxx --dns '1.1.1.1' --mount source=thorbot-session-data-vol,target=/session_data thornode-telegram-alert-bot
```
Replace the `--env` flag with your telegram token. 

The `--dns` flag tells the container to use cloudflare's dns server. 
We found that cloudflare is a bit faster than the preset dns server.

Finally, the `--mount` flag tells the container to mount our previously created volume
in the folder /session_data. This is exactly the folder where our 
bot expects to save and retrieve the session_data file.