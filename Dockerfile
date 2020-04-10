FROM python:3

VOLUME session_data

ADD thornode_alert.py /
ADD constants.py /

RUN pip install python-telegram-bot
RUN pip install requests

CMD [ "python", "./thornode_alert.py" ]
