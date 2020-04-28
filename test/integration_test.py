import copy
import json
import time
import os
import itertools
import random

from subprocess import Popen
from pyrogram import Client as TelegramClient


if os.path.exists("../storage/session.data"):
    os.remove("../storage/session.data")

thornode_bot_process = Popen(['python3', 'thornode_bot.py'], cwd="../")

telegram = TelegramClient(
    "my_account",
    api_id=os.environ['TELEGRAM_API_ID'],
    api_hash=os.environ['TELEGRAM_API_HASH']
)

# We got an address from our mock api json file.
# This address will be recognized as valid by our bot and used throughout the tests.
VALID_ADDRESS = json.load(open('nodeaccounts.json'))[0]['node_address']

BOT_ID = os.environ['TELEGRAM_BOT_ID']


def test_start():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    assert response.reply_markup.inline_keyboard[0][0].text == "Add THORNode", "Add THORNode not visible after /start"
    print("/start ✅")
    print("------------------------")


def test_show_stats(expected_response):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    setup_response = next(telegram.iter_history(BOT_ID))
    setup_response.click(VALID_ADDRESS)
    time.sleep(3)
    setup_response = next(telegram.iter_history(BOT_ID))

    setup_response.click("Show THORNode Stats")
    time.sleep(3)

    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                     "'\n but got \n'" + first_response.text + "'"
    assert second_response.text == "Choose an address from the list below or add one:", \
        "Choose an address from the list below or add one: - not visible after Show THORNode Stats"

    print("Show THORNode Stats with " + VALID_ADDRESS + " ✅")
    print("------------------------")


def test_add_address(address, expected_response1, expected_response2):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    setup_response = next(telegram.iter_history(BOT_ID))

    setup_response.click("Add THORNode")
    time.sleep(3)
    first_response = next(telegram.iter_history(BOT_ID))
    telegram.send_message(BOT_ID, address)
    time.sleep(3)
    second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    assert first_response.text == expected_response1, "Expected '" + expected_response1 + "' but got '" + first_response.text + "'"
    assert second_response_1.text == expected_response2 or second_response_2.text == expected_response2, \
        "Expected '" + expected_response2 + "' but got '" + second_response_1.text + "' and '" + second_response_2.text + "'"
    print("Add THORNode with " + address + " ✅")
    print("------------------------")


def test_thornode_detail():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    setup_response = next(telegram.iter_history(BOT_ID))
    setup_response.click(VALID_ADDRESS)
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))

    assert response.text == "You chose\n" + VALID_ADDRESS + "\nWhat do you want to do with that Node?", \
        "Thornode Details not showing the right text"
    assert response.reply_markup.inline_keyboard[0][0].text == "Show THORNode Stats", "Show THORNode Stats Button not in Thornode Details"
    assert response.reply_markup.inline_keyboard[0][1].text == "<< Back", "<< Back Show Button not in Thornode Details"

    print("Thornode Details with " + VALID_ADDRESS + " ✅")
    print("------------------------")


def test_back_button():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    setup_response = next(telegram.iter_history(BOT_ID))
    setup_response.click(VALID_ADDRESS)
    time.sleep(3)

    setup_response = next(telegram.iter_history(BOT_ID))
    setup_response.click("<< Back")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))

    assert response.text == "Choose an address from the list below or add one:", "Back Button doesn't work!"

    print("Back button with " + VALID_ADDRESS + " ✅")
    print("------------------------")


def test_thornode_notification(field):
    with open('nodeaccounts.json') as json_read_file:
        node_data_original = json.load(json_read_file)
        node_data_new = copy.deepcopy(node_data_original)

    new_value = str(random.randrange(0, 100))
    if field == 'node_address':
        new_value = 'thor' + new_value

    node_data_new[0][field] = new_value

    with open('nodeaccounts.json', 'w') as json_write_file:
        json.dump(node_data_new, json_write_file)

    time.sleep(40)
    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

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
    assert second_response.text == "Choose an address from the list below or add one:", \
        "Choose an address from the list below or add one: - not visible after Show THORNode Stats"
    print("Notification Thornode data change with " + field + " ✅")
    print("------------------------")


def test_block_height_notification():
    with open('status.json') as json_read_file:
        node_data = json.load(json_read_file)

    block_height = node_data['result']['sync_info']['latest_block_height']
    new_block_height = int(block_height) - 200
    node_data['result']['sync_info']['latest_block_height'] = str(new_block_height)

    time.sleep(40)
    with open('status.json', 'w') as json_write_file:
        json.dump(node_data, json_write_file)
    time.sleep(30)

    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    expected_response = 'Block height is not increasing anymore!'

    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "Choose an address from the list below or add one:", \
        "Choose an address from the list below or add one: - not visible after block height notification"

    time.sleep(70)
    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    expected_response = 'Block height is increasing again!'

    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "Choose an address from the list below or add one:", \
        "Choose an address from the list below or add one: - not visible after block height notification"
    print("Check Blockchain Height ✅")
    print("------------------------")


def test_midgard_notification():
    with open('midgard.json', 'w') as write_file:
        write_file.write('"FAIL"')
    time.sleep(40)
    
    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    expected_response = 'Midgard API is not healthy anymore'
    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "Choose an address from the list below or add one:", \
        "Choose an address from the list below or add one: - not visible after block height notification"

    with open('midgard.json', 'w') as write_file:
        write_file.write('"OK"')
    time.sleep(40)
    
    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    expected_response = 'Midgard API is healthy again'
    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "Choose an address from the list below or add one:", \
        "Choose an address from the list below or add one: - not visible after block height notification"


with telegram:
    try:
        time.sleep(5)
        test_start()
        test_add_address(address="invalidAddress",
                         expected_response1="What's the address of your THORNode? (enter /cancel to return to the menu)",
                         expected_response2="⛔️ I have not found a THORNode with this address! Please try another one. "
                                            "(enter /cancel to return to the menu)")
        test_add_address(address="/cancel",
                         expected_response1="What's the address of your THORNode? (enter /cancel to return to the menu)",
                         expected_response2="Choose an address from the list below or add one:")
        test_add_address(address=VALID_ADDRESS,
                         expected_response1="What's the address of your THORNode? (enter /cancel to return to the menu)",
                         expected_response2="Got it! 👌")
        test_thornode_detail()
        test_back_button()
        test_show_stats(expected_response="THORNode: " + VALID_ADDRESS)
        test_thornode_notification(field="status")
        test_thornode_notification(field="bond")
        test_thornode_notification(field="slash_points")
        test_thornode_notification(field="node_address")
        test_block_height_notification()
        test_midgard_notification()

        print("✅ -----ALL TESTS PASSED----- ✅")

    except AssertionError as e:
        print("💥 Assertion Error: 💥")
        print(e)
        print("💥 --> Shutting done Thornode Bot Process, Mock API Server Process and Telegram Client... 💥")
    finally:
        thornode_bot_process.terminate()
