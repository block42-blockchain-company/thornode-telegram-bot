FROM python:3.7

VOLUME storage

ADD thornode_bot.py /
ADD constants.py /

RUN pip install -r requirements.txt

CMD [ "python", "./thornode_bot.py" ]