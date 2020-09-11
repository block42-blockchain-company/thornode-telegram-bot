FROM ubuntu:18.04

ADD . /

RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y python3-pip
RUN apt-get install -y python3.7
RUN python3.7 -m pip install pip

RUN python3.7 -m pip install -r requirements.txt

CMD [ "python3.7", "bot/thornode_bot.py" ]
