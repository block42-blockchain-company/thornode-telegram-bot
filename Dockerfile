FROM python:3.7

RUN mkdir /storage
RUN mkdir /test

ADD thornode_bot.py/ /
ADD requirements.txt/ /
ADD test/nodeaccounts.json /test
ADD test/integration_test.py /test

RUN pip install -r requirements.txt

CMD [ "python", "./thornode_bot.py" ]