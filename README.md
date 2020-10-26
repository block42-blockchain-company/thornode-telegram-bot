# thornode-telegram-bot ⚡🤖
A telegram bot to monitor the status of THORNodes.

If you have questions feel free to open a github issue or contact us in our Telegram Channel https://t.me/block42_crypto!

## Requirements
* Telegram
* Kubectl (if you want to run with Kubernetes)
* Docker (if you want to run with docker or docker-compose)
* Docker Compose (if you want to run with docker-compose)
* Python3 (if you want to run without docker)

## Quickstart
For *kubernetes* open `kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml` and/or 
`kubernetes/k8s_thornode_bot_deployment_testnet.yaml` file;

### Environmental variables
For *docker-compose* open `variables-chaosnet.env` and/or
 `variables-testnet.env` file and set:
 
- `TELEGRAM_BOT_TOKEN` to your Telegram Bot Token obtained from BotFather.
- `NETWORK_TYPE` to either `TESTNET` or `CHAOSNET`.
- `BINANCE_NODE_IPS` to a list of Binance Node IPs you want to monitor (or `localhost`).
Leave it empty or remove it to not monitor any Binance Node.
- `ETHEREUM_NODE_IPS` to a list of Ethereum Node IPs you want to monitor (or `localhost`).
Leave it empty or remove it to not monitor any Ethereum Node.
- `ADMIN_USER_IDS` to a list of Telegram User IDs that are permitted to access the 
Bot. Set it to `ALL` to make it available to everybody
- `BITCOIN_NODE_IPS` to a list of Bitcoin Node IPs you want to monitor (or `localhost`).
Leave it empty or remove it to not monitor any Bitcoin Node.
- `BITCOIN_NODE_USERNAMES` to corresponding usernames for each Bitcoin node ip to  
[json-rpc API](https://en.bitcoin.it/wiki/API_reference_(JSON-RPC)).
- `BITCOIN_NODE_PASSWORDS` to corresponding passwords for each Bitcoin node ip to 
[json-rpc API](https://en.bitcoin.it/wiki/API_reference_(JSON-RPC)).

### Kubernetes (K8s)

*We assume that you already have a running K8s cluster.*

Install the same `kubectl` version you use in your K8s cluster (one major version difference is alright).

Download the cluster config file from your K8s provider and set the path of it to the `KUBECONFIG` environment 
variable:
```
export KUBECONFIG=/your/path/to/the/moon/k8s-kubeconfig.yaml
```

Now, from the project's main directoty, run 
```
# One Bot on Chaosnet:
kubectl create -f kubernetes/k8s_setup_chaosnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml

# One Bot on Testnet:
kubectl create -f kubernetes/k8s_setup_testnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml

# Two Bots on both networks:
kubectl create -f kubernetes/k8s_setup_chaosnet.yaml -f kubernetes/k8s_setup_testnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml
```


### Docker-compose

Install `docker` and `docker-compose` and run:

```
# One Bot on Chaosnet:
docker-compose -f docker-compose-chaosnet.yaml up -d

# One Bot on Testnet:
docker-compose -f docker-compose-testnet.yaml up -d

# Two Bots on both networks:
docker-compose -f docker-compose-testnet.yaml -f docker-compose-chaosnet.yaml up -d
```

## Steps to run everything yourself
* [Install dependencies](#install-dependencies)
* [Create Telegram bot token via BotFather](#create-telegram-bot-token-via-botfather)
* [Set environment variables](#set-environment-variables)
* [Start the bot](#start-the-bot)
* [Run and test the bot](#run-and-test-the-bot)
* [Production](#production)
  * [Kubernetes](#kubernetes)
    * [K8s-Setup](#k8s-setup)
    * [Modifying running K8s-Bot](#modifying-running-k8s-bot)
  * [Docker Standalone](#docker-standalone)
  * [Docker Compose](#docker-compose)
* [Testing](#testing)

## [Install dependencies](#install-dependencies)
Install all required dependencies via: `pip install -r requirements.txt`

## [Create Telegram bot token via BotFather](#create-telegram-bot-token-via-botfather)
Start a Telegram chat with [BotFather](https://t.me/BotFather) and click `start`.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token. Save this token, you will need it in a second.

## [Set environment variables](#set-environment-variables)
Set the telegram bot token you just created as an environment variable: `TELEGRAM_BOT_TOKEN`

```
export TELEGRAM_BOT_TOKEN=XXX
```
---
Set the network you want to monitor:
```
export NETWORK_TYPE=XXX
```
You can set it to `TESTNET` or `CHAOSNET`. If you leave this empty or write it wrong, testnet will be 
monitored by default.
---
#### Other nodes - Binance, Bitcoin, Ethereum supported
**If you don't have any additional nodes to monitor, just don't set these variables.**

If you enter multiple node IPs for one network make sure to separate the IDs with comma (`,`).
Set it to `localhost` if the Node runs on the same machine as the Telegram Bot.
##### Binance
```
export BINANCE_NODE_IPS=3.228.22.197,localhost
```
##### Ethereum
```
export ETHEREUM_NODE_IPS=3.228.22.197,localhost
```
##### Bitcoin
For each node ip you need to set the corresponding usernames and passwords to your node's
[json-rpc API](https://en.bitcoin.it/wiki/API_reference_(JSON-RPC)).
 In result, for `n` bitcoin node ips you must set `n` usernames and `n` passwords.
```
export BITCOIN_NODE_IPS=ip_1,ip_2
export BITCOIN_NODE_USERNAMES=username_to_ip_1,username_to_ip_2
export BITCOIN_NODE_PASSWORDS=password_to_ip_1,password_to_ip_2
```
---
Next set Telegram User IDs that are permissioned to access the Bot in the `ADMIN_USER_IDS` environment variable.
Set the variable to `ADMIN_USER_IDS=ALL`, to make the Bot accessible for anybody.

To find out your Telegram ID, open your Telegram Client, and search for the Telegram Bot `@userinfobot`.
Ensure that this is a Bot and not a Channel and has exactly the handle `@userinfobot`, as there
are a lot of channels and bots with similar names.
Start this Bot and it returns you your User ID that you need to export in `ADMIN_USER_IDS`.

If you enter multiple User IDs, make sure to separate the IDs with `,` i.e. a comma.
```
export ADMIN_USER_IDS=12345,56789,42424
```
---
Finally, if you want test the Thornode Telegram Bot with data from your local machine, you
need to set the debug environment variable:
```
export DEBUG=True
```
The DEBUG flag set to True will run a local web server as a separate process. 
This way the telegram bot can access the local files `nodeaccounts.json` and `status.json`
in the `test/mock_files` folder. Verify that Python is available via command `python3` in your environment.
Furthermore, the server mocks a few Thorchain specific endpoints, for this reason please make sure that the ports: 
* `localhost:26657`
* `localhost:8080`

are not busy on your machine. Otherwise, mock server won't start.


To test whether the bot actually notifies you about changes, the data the bot is querying needs to change. 
You can simulate that by manually editing `nodeaccounts.json`, `status.json`
 and `midgard.json` in `test/mock_files` directory.

Furthermore, in DEBUG mode a separate process runs `test/increase_block_height.py` which artificially increases
the block height so that there are no notifications that the block height got stuck.

---
If you are using a Jetbrains IDE (e.g. Pycharm), you can set these environment variables for your run 
configuration which is very convenient for development 
(see: https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm).


## [Start the bot](#start-the-bot)
Start the bot via:

```
python3 thornode_bot.py
```

Make sure that you see a message in the console which indicates that the bot is running.

## [Run and test the bot](#run-and-test-the-bot)
When you created the telegram bot token via BotFather, you gave your bot a certain name (e.g. `thornode_bot`). Now search for this name in Telegram,
open the chat and hit start!

At this point, you can play with the bot, see what it does and check that everything works fine!

The bot persists all data, which means it stores its chat data in the file `storage/session.data`.  Once you stop and restart the bot,
everything should continue as if the bot was never stopped.

If you want to reset your bot's data, simply delete the file `session.data` in the `storage` directory before startup.

## [Production](#production)
In production, you do not want to use mock data from the local endpoint but real network data. 
To get real data just set `DEBUG=False` and all other environment variables as 
described in the 'Set environment variables' section.

If you're using kubernetes to run this Bot, modify the existing variables in `kubernetes/k8s_thornode_bot_deployment.yaml` file.
To use docker-compose, modify the existing variables in `variables.env` file (No need to
set DEBUG as there's no DEBUG mode in the k8s or docker version). 

### [Kubernetes](#kubernetes)
*We assume that you already have a running Kubernetes (K8s) cluster running in the cloud or on-premise.*

As many node operators deploy all thorchain components via K8s, it makes sense to run the Bot in the same K8s cluster.
Our solution should run on all K8s clusters (AWS, Digital Ocean, on-premise...)

#### [K8s-Setup](#k8s-setup)

All K8s files can be found in `/kubernetes`.

The `k8s_setup_*.yaml` files define the namespace in which the bot(s) operates, as well as the persistent volume claim(s)
that ensures user data is persisted across bot restarts.

In the `k8s_thornode_bot_deployment-*.yaml` files you find the deployment of the actual bot(s).
These are the files where you have to insert the correct values for the environment variables.

Set the right values as indicated by the comments.

After that install the kubernetes command line control `kubectl`.
Check out the K8s version of your running cluster, and install a `kubectl` version that is within 
one major version of your cluster (e.g. cluster is 1.17.4, install for `kubectl` either 1.16.X, 1.17.X or 1.18.X).

To connect to your cluster, first download the cluster config file from your K8s provider.
Then set the path of the config file to the `KUBECONFIG` environment variable:
```
export KUBECONFIG=/your/path/to/the/moon/k8s-kubeconfig.yaml
```

Now create first the setup manifest, and then the deployment manifest with:
```
# One Bot on Chaosnet:
kubectl create -f kubernetes/k8s_setup_chaosnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml

# One Bot on Testnet:
kubectl create -f kubernetes/k8s_setup_testnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml

# Two Bots on both networks:
kubectl create -f kubernetes/k8s_setup_chaosnet.yaml -f kubernetes/k8s_setup_testnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml
```

Check out if your deployment and persistent volume claim were succesfully created with:
```
kubectl get pods -n thornode-bot
kubectl get pvc -n thornode-bot
``` 

#### [Modifying running K8s-Bot](#modifying-running-k8s-bot)

At a later point you might want to update the environment variables, or use the latest docker image.
For the former, modify `kubernetes/k8s_thornode_bot_deployment-*.yaml` as desired.

Then delete the deployment, and create it again:
```
# One Bot on Chaosnet:
kubectl delete -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml

# One Bot on Testnet:
kubectl delete -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml

# Two Bots on both networks:
kubectl delete -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml
kubectl create -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml
```

Your bot(s) should send you a message that he got updated. 
He now uses the new environment variables / newest docker image.

---

If you want to delete all k8s resources related to the bot(s) (namespace and persistent volume with user data), 
first delete the deployment and then the setup:
```
# One Bot on Chaosnet:
kubectl delete -f kubernetes/k8s_setup_chaosnet.yaml
kubectl delete -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml

# One Bot on Testnet:
kubectl delete -f kubernetes/k8s_setup_testnet.yaml
kubectl delete -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml

# Two Bots on both networks:
kubectl delete -f kubernetes/k8s_setup_chaosnet.yaml -f kubernetes/k8s_setup_testnet.yaml
kubectl delete -f kubernetes/k8s_thornode_bot_deployment_chaosnet.yaml -f kubernetes/k8s_thornode_bot_deployment_testnet.yaml
```

### [Docker Standalone](#docker-standalone)
To run the bot as a docker container, make sure you have docker installed (see: https://docs.docker.com/get-docker).

Navigate to the root directory of this repository and execute the following commands:

Build the docker image as described in the `Dockerfile`:

```
docker build -t thornode-bot .
```

To make the bot's data persistent, you need to create a docker volume.
If the bot crashes or restarts the volume won't be affected and keeps all the session data:

```
docker volume create thornode-bot-volume
```

Finally, run the docker container:

```
docker run --env TELEGRAM_BOT_TOKEN=XXX --env BINANCE_NODE_IPS=XXX --mount source=thornode-bot-volume,target=/storage thornode-bot
```

Set the `--env TELEGRAM_BOT_TOKEN` flag to your telegram bot token. 

Set the `--env NETWORK_TYPE` flag to the network you want to monitor (`TESTNET` or `CHAOSNET` while 
the former is the default).

If you have a node that you want to monitor, set additional node variables (see [Set environment variables](#set-environment-variables) section). 
Set it as `BINANCE_NODE_IPS` in above example.

Finally, the `--mount` flag tells docker to mount our previously created volume in the directory `storage`. 
This is the directory where your bot saves and retrieves the `session.data` file.

*Please note that as docker is intended for production,
there is not the possibility for the `DEBUG` mode when using docker.*


### [Docker Compose](#docker-compose)
The explained steps in the Docker Standalone section are conveniently bundled into the files
`docker-compose-chaosnet.yaml` and `docker-compose-testnet.yaml`.

First, as before, you need to set the right values in the `variables-chaosnet.env` and/or
`variables-testnet.env` files for `TELEGRAM_BOT_TOKEN`, `ADMIN_USER_IDS` and additional nodes.

If you don't want to spin up the official docker image from our dockerhub, open any of the 
`docker-compose-*.yaml` and comment out the line `image: "block42blockchaincompany/thornode_bot:latest"`
and comment in the line `build: .`.

Finally, start the Thornode Telegram Bot with `docker-compose up -d`, and specify the correct file with the `-f` flag:
```
# One Bot on Chaosnet:
docker-compose -f docker-compose-chaosnet.yaml up -d

# One Bot on Testnet:
docker-compose -f docker-compose-testnet.yaml up -d

# Two Bots on both networks:
docker-compose -f docker-compose-testnet.yaml -f docker-compose-chaosnet.yaml up -d
```

If you want to stop your bot(s) later again, run `docker-compose down`, and specify the correct file with the `-f` flag:
```
# One Bot on Chaosnet:
docker-compose -f docker-compose-chaosnet.yaml down

# One Bot on Testnet:
docker-compose -f docker-compose-testnet.yaml down

# Two Bots on both networks:
docker-compose -f docker-compose-testnet.yaml -f docker-compose-chaosnet.yaml down
```

---

If you have problems running 'docker-compose up' while using a VPN, 
try to this:
- First run in your console
```
docker network create vpnworkaround --subnet 10.0.1.0/24
```
* Then comment in the networks configuration in any `docker-compose-*.yaml`
```
networks:
  default:
    external:
      name: vpnworkaround
```
* Run again in your terminal
```
docker-compose up -f docker-compose-*.yaml -d
```

This solution is taken from https://github.com/docker/for-linux/issues/418#issuecomment-491323611



## [Testing](#testing)
To test the Thornode Bot, you need to impersonate your own Telegram Client programmatically.

To do that, you need to obtain your API ID and API hash by creating a 
telegram application that uses your user identity on https://my.telegram.org .
Simply login in with your phone number that is registered on telegram, 
then choose any application (we chose Android) and follow the steps. 

Once you get access to `api_id` and `api_hash`, save them in the Environment variables
Afterwards run `python3 test/sign_in_telegram.py`. This asks
you to put in your phone number, verifies your telegram client and creates the verification
file `test/telegram_session.string`. This file is needed by the testing suite
to impersonate your telegram client.

Once you get access to api_id and api_hash, save them in the Environment variables
`TELEGRAM_API_ID` and `TELEGRAM_API_HASH` respectively.
Also, save the name of your Telegram Bot without the preceding `@` 
in the `TELEGRAM_BOT_ID` environment variable (e.g. if your bot is named 
`@thornode_test_bot`, save `thornode_test_bot` in `TELEGRAM_BOT_ID`).

You also need to have set the `TELEGRAM_BOT_TOKEN` environment variable with your 
telegram bot token, set `ADMIN_USER_IDS` with permissioned IDs and
set `DEBUG=True` as explained in previous sections.

Keep in mind that the test always deletes the `session.data` file inside `storage/`
in order to have fresh starts for every integration test. If you wish to keep your
persistent data, don't run the integration test or comment out 
the line `os.remove(session_data_path)` in `test/integration_test.py`

To run the test open the `test/` folder in your terminal and run
```
python3 integration_test.py
```

The test should endure several minutes.
Every command succeded if you see `-----ALL TESTS PASSED-----` at the end.