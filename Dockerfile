FROM python:3.7

LABEL autoheal=true

RUN mkdir /storage
ADD healthcheck.py/ /

ADD thornode_bot.py/ /
ADD requirements.txt/ /

RUN pip install -r requirements.txt

HEALTHCHECK --start-period=10s --interval=10s --retries=2 --timeout=3s CMD [ "python", "./healthcheck.py" ]

CMD [ "python", "./thornode_bot.py" ]
