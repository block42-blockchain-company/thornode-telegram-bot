FROM python:3.7

RUN mkdir /storage

ADD thornode_bot.py/ /
ADD requirements.txt/ /

RUN pip install -r requirements.txt

CMD [ "python", "./thornode_bot.py" ]