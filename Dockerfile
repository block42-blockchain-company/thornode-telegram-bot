FROM python:3.7

LABEL autoheal=true

RUN mkdir /storage
ADD healthcheck.py/ /

ADD thornode_bot.py/ /
ADD requirements.txt/ /

RUN pip install -r requirements.txt

HEALTHCHECK --start-period=10s --interval=30s --retries=1 --timeout=3s CMD [ "python", "./healthcheck.py" ]

CMD [ "python", "./thornode_bot.py" ]
