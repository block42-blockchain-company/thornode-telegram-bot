import copy
import json
import time
import http.server
import os
import itertools
import random

from subprocess import Popen
from pyrogram import Client

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler


server = Popen(['python3', '-m', 'http.server', '8000', '--bind', '127.0.0.1'])

if os.path.exists("../storage/session.data"):
    os.remove("../storage/session.data")
thorbot = Popen(['python3', 'thornode_bot.py'], cwd="../")

app = Client(
    "my_account",
    api_id=os.environ['TELEGRAM_API_ID'],
    api_hash=os.environ['TELEGRAM_API_HASH']
)

with open('nodeaccounts.json') as json_read_file:
    node_data = json.load(json_read_file)
    VALID_ADDRESS = node_data[0]["node_address"]

chat_id = "THORnodeAlert_bot"


def start():
    app.send_message(chat_id, "/start")
    time.sleep(3)

    response = next(app.iter_history(chat_id))
    assert response.reply_markup.inline_keyboard[0][0].text == "Add THORNode", "Add THORNode not visible after /start"
    assert response.reply_markup.inline_keyboard[0][1].text == "Show THORNode Stats", \
        "Show THORNode Stats not visible after /start"
    print("/start - works as expected")
    print("------------------------")


def show_stats(expected_response):
    app.send_message(chat_id, "/start")
    time.sleep(3)
    response = next(app.iter_history(chat_id))

    response.click("Show THORNode Stats")

    time.sleep(3)
    first_response = next(itertools.islice(app.iter_history(chat_id), 1, None))
    second_response = next(itertools.islice(app.iter_history(chat_id), 0, None))

    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                     "' but got '" + first_response.text + "'"
    assert second_response.text == "What do you want to do?", "What do you want to do? - " \
                                                              "not visible after Show THORNode Stats"
    print("Show THORNode Stats button - works as expected")
    print("------------------------")


def add_address(address, expected_response1, expected_response2):
    app.send_message(chat_id, "/start")
    time.sleep(3)
    response0 = next(app.iter_history(chat_id))

    response0.click("Add THORNode")
    time.sleep(3)
    response1 = next(app.iter_history(chat_id))
    app.send_message(chat_id, address)
    time.sleep(3)
    response2_first = next(itertools.islice(app.iter_history(chat_id), 1, None))
    response2_second = next(itertools.islice(app.iter_history(chat_id), 0, None))

    assert response1.text == expected_response1, "Expected '" + expected_response1 + "' but got '" + response1.text + "'"
    assert response2_first.text == expected_response2 or response2_second.text == expected_response2, \
        "Expected '" + expected_response2 + "' but got '" + response2_first.text + "' and '" + response2_second.text + "'"
    print("Add THORNode button - works as expected with " + address)
    print("------------------------")


def notify(field):
    with open('nodeaccounts.json') as json_read_file:
        node_data_original = json.load(json_read_file)
        node_data_new = copy.deepcopy(node_data_original)

    new_value = str(random.randrange(0, 100))
    node_data_new[0][field] = new_value

    with open('nodeaccounts.json', 'w') as json_write_file:
        json.dump(node_data_new, json_write_file)

    time.sleep(40)
    first_response = next(itertools.islice(app.iter_history(chat_id), 1, None))
    second_response = next(itertools.islice(app.iter_history(chat_id), 0, None))

    if field == "node_address":
        expected_response = 'THORNode is not active anymore! 💀' + '\n' + \
                           'Address: ' + node_data_original[0]['node_address'] + '\n\n' + \
                           'Please enter another THORNode address.'
    else:
        expected_response = 'THORNode: ' + node_data_original[0]['node_address'] + '\n' + \
                   'Status: ' + node_data_original[0]['status'].capitalize() + ' ➡️ ' + node_data_new[0]['status'].capitalize() + '\n' + \
                   'Bond: ' + '{:,} RUNE'.format(int(node_data_original[0]['bond'])) + ' ➡️ ' + '{:,} RUNE'.format(int(node_data_new[0]['bond'])) + '\n' + \
                   'Slash Points: ' + '{:,}'.format(int(node_data_original[0]['slash_points'])) + ' ➡️ ' + '{:,}'.format(int(node_data_new[0]['slash_points']))

    assert first_response.text.find(expected_response) != -1, \
        "Expected '" + expected_response + "' but got '" + first_response.text + "'"
    assert second_response.text == "What do you want to do?", "What do you want to do? - " \
                                                              "not visible after Show THORNode Stats"
    print("Notification Thornode data change - works with " + field)


with app:
    try:
        time.sleep(5)
        start()
        show_stats("You have not told me about your THORNode yet. Please add one!")
        add_address("invalidAddress",
                    "What's the address of your THORNode? (enter /cancel to return to the menu)",
                    "⛔️ I have not found a THORNode with this address! Please try another one. "
                    "(enter /cancel to return to the menu)")
        add_address("/cancel",
                    "What's the address of your THORNode? (enter /cancel to return to the menu)",
                    "What do you want to do?")
        add_address(VALID_ADDRESS,
                    "What's the address of your THORNode? (enter /cancel to return to the menu)",
                    "Got it! 👌")
        add_address(VALID_ADDRESS,
                    '⚠️ This will override this THORNode: ' + VALID_ADDRESS + '\n\n'
                    'What\'s the address of your THORNode? (enter /cancel to return to the menu)',
                    "Got it! 👌")
        show_stats("THORNode: " + VALID_ADDRESS)
        notify("status")
        notify("bond")
        notify("slash_points")
        notify("node_address")
        show_stats('THORNode is not active anymore! 💀' + '\n' + \
                   'Address: ' + VALID_ADDRESS + '\n\n' + \
                   'Please enter another THORNode address.')

        print("-----ALL TESTS PASSED-----")

    except AssertionError as e:
        print("Assertion Error: ")
        print(e)
        print("--> Shutting done Thorbot, Server and Telegram Client...")
    finally:
        thorbot.terminate()
        server.kill()



