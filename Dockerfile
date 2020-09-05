FROM ubuntu:18.04

LABEL autoheal=true

ADD . /

RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y python3-pip
RUN apt-get install -y python3.7
RUN python3.7 -m pip install pip

RUN python3.7 -m pip install -r requirements.txt

HEALTHCHECK --start-period=10s --interval=10s --retries=2 --timeout=3s CMD [ "python3.7", "scripts/healthcheck.py" ]

CMD [ "python3.7", "bot/thornode_bot.py" ]
