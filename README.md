# thorchain-telegram-monitoring
A telegram bot to monitor the status of Thorchain Nodes.

Requirements:
* python3 installed
* telegram client available

Steps to run this repo:
* Install python-telegram-bot library
* Create Telegram Bot Token via BotFather
* Put Telegram Token in Environment variable
* Start local Thornode endpoint
* Start the bot
* Try the bot out

##Install python-telegram-bot library
In your terminal type `pip install python-telegram-bot`
Alternatively you can add the module in your IDE as described by the vendor.

## Create Telegram Bot Token via BotFather
In your telegram client, search in the search field for `botfather`.
Click on the account `BotFather`, and click `start` to start the chat.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token.
Save this token in a secure location (for example in an environment variable ;).

## Put Telegram Token in Environment variable
Save the above created telegram token in the environment variable `TELEGRAM_TOKEN`.

To do this, in your terminal type `export TELEGRAM_TOKEN=1234567890:xxxYourTokenxxxxx`, where
the value after the `=` should be your own token.

Alternatively, if your using a Jetbrains IDE like Pycharm, you can set this environment variable
for your configuration, which is convenient for development
(https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm).

## Start local Thornode endpoint
To test out whether the bot actually notifies you when there's a change in status, bond or slash_points,
we need a way to manipulate the data the bot is fetching.

We do that with the local json file `node_data.json`.

Go to the directory of this repo in your terminal, and start a local server with 
```
python3 -m http.server 8000 --bind 127.0.0.1
```

If the server works, this URL returns you the content of node_data.json:
```
http://localhost:8000/node_data.json
```

## Start the bot
Yes man, now is the great moment!

Open the directory in your terminal, and start the bot via
```
python3 thornode_alert.py
```

You should read one warning, and `INFO - THORnode Telegram Alert Bot is running...`

## Try the bot out
When you created the telegram token via BotFather, you gave your Bot a name.
Now search for this name in your telegram client, open the chat and hit start!

At this point, you can play with the bot, see what it does and assert that it does the right thing!

This bot is persistent, which means that it stores data in the file `session_data`. 
Once you stop the bot and restart it again, the functionality should continue as if the 
bot was never stopped.

If you don't want the bot to be persistent, simply delete the file `session_data`.