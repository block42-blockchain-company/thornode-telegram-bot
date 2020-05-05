# thornode-telegram-bot ⚡🤖
A telegram bot to monitor the status of THORNodes.

## Requirements
* Telegram
* Docker (if you want to run with docker or docker-compose)
* Docker Compose (if you want to run with docker-compose)
* Python3 (if you want to run without docker)

## Quickstart

Open `variables.env` file and set
- `TELEGRAM_BOT_TOKEN` to your Telegram Bot Token obtained from BotFather.
- `NODE_IP` to any IP you want to monitor. Leave `NODE_IP=localhost` to monitor your own local Node.
If you don't know any IP, set `NODE_IP` to a seed node IP from https://testnet-seed.thorchain.info .

Install `docker` and `docker-compose` and run:

```
docker-compose up -d
```

## Steps to run everything yourself
* Install dependencies
* Create Telegram bot token via [BotFather](https://t.me/BotFather)
* Set environment variables
* Start the bot
* Run & test the bot
* Production
* Testing

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

Next you can specify the IP of the Node that you want to watch in `NODE_IP` environment variable.
Leave this environment variable unset to listen on `localhost`.
If you don't know any IPs of Nodes, take one of the seed nodes from https://testnet-seed.thorchain.info .
```
export NODE_IP=3.228.22.197
```

Finally, if you want test the Thornode Telegram Bot with data from your local machine, you
need to set the debug environment variable:
```
export DEBUG=True
```
The DEBUG flag set to True will run a local web server as a separate process. 
This way the telegram bot can access the local files `nodeaccounts.json` und `status.json`
in the `test/` folder.

To test whether the bot actually notifies you about changes, the data the bot is quering needs to change. 
You can simulate that by manually editing `test/nodeaccounts.json`.

Futhermore in DEBUG mode a separate process runs `increase_block_height.py` which artificially increases
the block height so that there are no notifications that the block height got stuck.


If your using a Jetbrains IDE (e.g. Pycharm), you can set these environment variables for your run configuration which is very convenient for development (see: https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm).


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
In production you do not want to use mock data from the local endpoint but real network data. 
To get real data just set `DEBUG=False` in your environment variables and the bot will use available seed nodes for data retrieval.

### Docker Standalone
To run the bot as a docker container, make sure you have docker installed (see: https://docs.docker.com/get-docker).

Navigate to the root directory of this repository and execute the following commands:

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
docker run --env TELEGRAM_BOT_TOKEN=XXX --env NODE_IP=XXX --mount source=thornode-bot-volume,target=/storage thornode-bot
```

Set the `--env TELEGRAM_BOT_TOKEN` flag to your telegram bot token. 

Set the `-env NODE_IP` flag to an IP of a running node, or remove 
`--env NODE_IP=XXX` to listen on localhost. 
If you don't know any IP, set `NODE_IP` to a seed node IP from https://testnet-seed.thorchain.info .

Finally, the `--mount` flag tells docker to mount our previously created volume in the directory `storage`. 
This is the directory where your bot saves and retrieves the `session.data` file.

*Please note that as docker is intended for production,
there is not the possibility for the `DEBUG` mode when using docker.*


#### Healthcheck
There is a health check in the Dockerfile that runs the `healthcheck.py` file.
The script assures that `thornode_bot.py` is periodically updating the `health.check` file.

If the docker health check fails, the docker container is marked as "unhealthy". 
However, when using docker standalone (without docker compose or docker swarm) this doesn't do anything.
To restart unhealthy containers, we have to use the autoheal image https://hub.docker.com/r/willfarrell/autoheal/ .

To make sure a potentially unhealthy thorbot_node container is restarted, run the autoheal container alongside the
thornode_bot container:
```
docker run -d --name autoheal --restart=always -v /var/run/docker.sock:/var/run/docker.sock willfarrell/autoheal
```

### Docker Compose
The explained steps in the Docker Standalone section are conveniently bundled into a
`docker-compose.yaml` file.

First, as before, you need to set the right values in the `variables.env` file for `TELEGRAM_BOT_TOKEN`
and `NODE_IP`.

If you don't want to spin up the official docker image from our dockerhub, open 
`docker-compose.yaml` and comment out the line `image: "block42blockchaincompany/thornode_bot:release-1.3"`
and comment in the line `build: .`.

Finally, start the Thornode Telegram Bot with:
```
docker-compose up -d
```

---

If you have problems running 'docker-compose up' while using a VPN, 
try to this:
- First run in your console
```
docker network create vpnworkaround --subnet 10.0.1.0/24
```
* Then comment in the networks configuration in `docker-compose.yaml`
```
networks:
  default:
    external:
      name: vpnworkaround
```
* Run again in your terminal
```
docker-compose up -d
```

This solution is taken from https://github.com/docker/for-linux/issues/418#issuecomment-491323611




## Testing
To test the Thornode Bot, you need to impersonate your own Telegram Client programmatically.

To do that, you need to obtain your API ID and API hash by creating a 
telegram application that uses your user identity on https://my.telegram.org .
Simply login in with your phone number that is registered on telegram, 
then choose any application (we chose Android) and follow the steps. 

Once you get access to api_id and api_hash, save them in the Environment variables
`TELEGRAM_API_ID` and `TELEGRAM_API_HASH` respectively.

You also need to have set the `TELEGRAM_BOT_TOKEN` environment variable with your 
telegram bot token and set `DEBUG=True` as explained in previous sections.

Keep in mind that the test always deletes the `session.data` file inside `storage/`
in order to have fresh starts for every integration test. If you wish to keep your
persistent data, don't run the integration test or comment out 
the line `os.remove("../storage/session.data")` in integration_test.py

To run the test open the `test/` folder in your terminal and run
```
python3 integration_test.py
```

The test should endure several minutes.
Every command succeded if you see `-----ALL TESTS PASSED-----` at the end.