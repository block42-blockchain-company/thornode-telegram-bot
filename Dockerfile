FROM ubuntu:18.04

LABEL autoheal=true

ADD . /

RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y python3.7
RUN apt-get install -y python3-pip

RUN pip3 install -r requirements.txt

HEALTHCHECK --start-period=10s --interval=10s --retries=2 --timeout=3s CMD [ "python3", "scripts/healthcheck.py" ]

CMD [ "python3", "bot/thornode_bot.py" ]
