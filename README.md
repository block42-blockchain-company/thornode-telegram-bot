# thornode-telegram-bot
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

## Install python-telegram-bot library
In your terminal type `pip install python-telegram-bot`. Alternatively you can add the module in your IDE as described by the vendor.

## Create Telegram bot token via BotFather
Start a Telegram chat with [BotFather](https://t.me/BotFather) and click `start`.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token. Save this token in a secure location (for example in an environment variable ;).

## Set Telegram token as environment variable
Save the above created telegram token in the environment variable `TELEGRAM_TOKEN`.

To do this, in your terminal type `export TELEGRAM_TOKEN=1234567890:xxxYourTokenxxxxx`, where
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

This bot is persistent, which means, it stores data in the file `session_data/session_data`.  Once you stop and restart the bot again, everything should continue as if the bot was never stopped (because of the persisting the session data).

If you don't want the bot to be persistent, simply delete the file `session_data` in the `session_data` folder before startup.

## Production
For production you use real THORNode data, not from the local python endpoint.

Comment out this line `return HARDCODED_LOCAL_NODE`. The return statement below returns the IP address to get values from the testnet.
