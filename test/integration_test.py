import copy
import json
import time
import os
import itertools
import random

from subprocess import Popen
from pyrogram import Client as TelegramClient

# Delete previous sessions for clean testing
if os.path.exists("../storage/session.data"):
    os.remove("../storage/session.data")

# Start the Telegram Thornode Bot
thornode_bot_process = Popen(['python3', 'thornode_bot.py'], cwd="../")


"""
######################################################################################################################################################
Static & environment variables
######################################################################################################################################################
"""

telegram = TelegramClient(
    "my_account",
    api_id=os.environ['TELEGRAM_API_ID'],
    api_hash=os.environ['TELEGRAM_API_HASH']
)

# We got an address from our mock api json file.
# This address will be recognized as valid by our bot and used throughout the tests.
VALID_ADDRESS = json.load(open('nodeaccounts.json'))[0]['node_address']

BOT_ID = os.environ['TELEGRAM_BOT_ID']

STATUS_EMOJIS = {"active": "💚", "standby": "📆", "deactive": "🔴"}

THORCHAIN, BINANCE = range(2)

"""
######################################################################################################################################################
TEST CASES
######################################################################################################################################################
"""


def test_start():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    assert response.reply_markup.inline_keyboard[0][0].text == "📡 MY NODES", "📡 MY NODES not visible after /start"
    assert response.reply_markup.inline_keyboard[1][0].text == "👀 SHOW ALL", "👀 SHOW ALL not visible after /start"
    assert response.reply_markup.inline_keyboard[1][1].text == "🗝 ADMIN AREA", "🗝 ADMIN AREA not visible after /start"
    print("/start ✅")
    print("------------------------")


def test_my_thornodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    click_button("📡 MY NODES")

    response = next(telegram.iter_history(BOT_ID))
    assert response.reply_markup.inline_keyboard[0][0].text == "➕ ADD ALL", "➕ ADD ALL not visible after clicking on 📡 MY NODES"
    assert response.reply_markup.inline_keyboard[0][1].text == "1️⃣ ADD NODE", "1️⃣ ADD NODE not visible after clicking on 📡 MY NODES"
    assert response.reply_markup.inline_keyboard[1][0].text == "➖ REMOVE ALL", "➖ REMOVE ALL not visible after clicking on 📡 MY NODES"
    assert response.reply_markup.inline_keyboard[1][1].text == "⬅️ BACK", "⬅️ BACK not visible after clicking on 📡 MY NODES"
    print("📡 MY NODES ✅")
    print("------------------------")


def test_back_button_my_thornodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    response = next(telegram.iter_history(BOT_ID))
    click_button("📡 MY NODES")

    assert_back_button(response.text)

    print("Back button in 📡 MY NODES ✅")
    print("------------------------")


def test_add_address(address, expected_response1, expected_response2):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("📡 MY NODES")

    click_button("1️⃣ ADD NODE")

    first_response = next(telegram.iter_history(BOT_ID))
    telegram.send_message(BOT_ID, address)
    time.sleep(3)
    second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    assert first_response.text == expected_response1, "Expected '" + expected_response1 + "' but got '" + first_response.text + "'"
    assert second_response_1.text == expected_response2 or second_response_2.text == expected_response2, \
        "Expected '" + expected_response2 + "' but got '" + second_response_1.text + "' and '" + second_response_2.text + "'"
    print("1️⃣ ADD NODE with " + address + " ✅")
    print("------------------------")


def test_thornode_detail():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("📡 MY NODES")
    
    click_button(STATUS_EMOJIS["deactive"] + " " + VALID_ADDRESS)

    response = next(telegram.iter_history(BOT_ID))

    number_of_unconfirmed_txs = json.load(open('unconfirmed_txs.json'))['result']['total']

    assert response.text.find("THORNode: " + VALID_ADDRESS) != -1, "Thornode Details not showing stats"
    assert response.text.find("Number of Unconfirmed Txs: " + number_of_unconfirmed_txs) != -1, \
        "Thornode Details not showing Number of unconfirmed Txs"
    assert response.reply_markup.inline_keyboard[0][0].text == "➖ REMOVE", \
        "➖ REMOVE Button not in Thornode Details"
    assert response.reply_markup.inline_keyboard[0][1].text == "⬅️ BACK", "⬅️ BACK Show Button not in Thornode Details"

    print("Thornode Details with " + VALID_ADDRESS + " ✅")
    print("------------------------")


def test_back_button_thornode_details():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("📡 MY NODES")

    response = next(telegram.iter_history(BOT_ID))

    click_button(STATUS_EMOJIS["deactive"] + " " + VALID_ADDRESS)
    assert_back_button(response.text)

    print("Back button in Thornode Details ✅")
    print("------------------------")


def test_delete_address(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("📡 MY NODES")
    click_button(STATUS_EMOJIS["deactive"] + " " + VALID_ADDRESS)

    click_button("➖ REMOVE")

    first_response = next(telegram.iter_history(BOT_ID))

    assert first_response.text == '⚠️ Do you really want to remove the address from your monitoring list? ⚠️' + VALID_ADDRESS, \
        "➖ REMOVE button doesn't work!"

    if confirm:
        click_button("YES ✅")
        time.sleep(3)
        second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
        second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))
        assert second_response_1.text == "❌ Thornode address got deleted! ❌\n" + VALID_ADDRESS, \
            "YES button on deletion confirmation does not yield deletion statement"
        assert second_response_2.text == "Choose an address from the list below or add one:", \
            "YES button on deletion confirmation does not go back to thornodes menu"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text == "➕ ADD ALL", "Node is NOT deleted after deletion"
    else:
        click_button("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text.find("THORNode: " + VALID_ADDRESS) != -1, \
            "NO button on single address deletion confirmation does not go back to Thornode details"
    print("➖ REMOVE Address with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_add_all_addresses(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("📡 MY NODES")
    click_button("➕ ADD ALL")

    first_response = next(telegram.iter_history(BOT_ID))

    assert first_response.text == '⚠️ Do you really want to add all available THORNodes to your monitoring list? ⚠️', \
        "➕ ADD ALL button does not work!"

    if confirm:
        click_button("YES ✅")
        second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
        second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))
        assert second_response_1.text == "Added all THORNodes! 👌", \
            "YES button on ➕ ADD ALL confirmation does not yield addition statement"
        assert second_response_2.text == "Choose an address from the list below or add one:", \
            "YES button on ➕ ADD ALL confirmation does not go back to 📡 MY NODES menu"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text == STATUS_EMOJIS["deactive"] + " " + VALID_ADDRESS and \
               second_response_2.reply_markup.inline_keyboard[1][0].text.find('thor') != -1,\
            "Nodes are not added after YES button on ➕ ADD ALL confirmation"
    else:
        click_button("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text == "Choose an address from the list below or add one:", \
            "NO button on ➕ ADD ALL confirmation does not go back to 📡 MY NODES menu"

    print("➕ ADD ALL with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_delete_all_addresses(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("📡 MY NODES")
    click_button("➖ REMOVE ALL")

    first_response = next(telegram.iter_history(BOT_ID))

    assert first_response.text == '⚠️ Do you really want to remove all THORNodes from your monitoring list? ⚠️', \
        "➖ REMOVE ALL button does not work!"

    if confirm:
        click_button("YES ✅")
        second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
        second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))
        assert second_response_1.text == "❌ Deleted all THORNodes! ❌", \
            "YES button on ➖ REMOVE ALL confirmation does not yield deletion statement"
        assert second_response_2.text == "Choose an address from the list below or add one:", \
            "YES button on ➖ REMOVE ALL confirmation does not go back to 📡 MY NODES menu"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text == '➕ ADD ALL' and \
               second_response_2.reply_markup.inline_keyboard[0][1].text == '1️⃣ ADD NODE', \
            "Nodes are not deleted after YES button on ➖ REMOVE ALL confirmation"
    else:
        click_button("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text == "Choose an address from the list below or add one:", \
            "NO button on ➖ REMOVE ALL confirmation does not go back to 📡 MY NODES menu"

    print("➖ REMOVE ALL with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_show_all_thorchain_nodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("👀 SHOW ALL")

    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    expected_response1 = 'Status of all THORNodes in the THORChain network:'
    expected_response2 = 'THORNode: ' + VALID_ADDRESS
    assert first_response.text.find(expected_response1) != -1, "Expected '" + expected_response1 + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert first_response.text.find(expected_response2) != -1, "Expected '" + expected_response2 + \
                                                               "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible 👀 SHOW ALL"
    print("👀 SHOW ALL ✅")
    print("------------------------")


def test_admin_area():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    click_button("🗝 ADMIN AREA")

    response = next(telegram.iter_history(BOT_ID))

    back_button_found = False
    for button in response.reply_markup.inline_keyboard:
        back_button_found = True if button[0].text == "⬅️ BACK" else False

    assert response.text.find("You're in the Admin Area - proceed with care") != -1, \
        "🗝 ADMIN AREA Message not visible after clicking on 🗝 ADMIN AREA"
    assert back_button_found, "⬅️ BACK not visible after clicking on 🗝 ADMIN AREA"

    print("🗝 ADMIN AREA ✅")
    print("------------------------")


def test_back_button_admin_area():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    click_button("🗝 ADMIN AREA")

    assert_back_button(response.text)

    print("Back button in 🗝 ADMIN AREA ✅")
    print("------------------------")


def test_restart_container(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("🗝 ADMIN AREA")
    setup_response = next(telegram.iter_history(BOT_ID))

    click_button(setup_response.reply_markup.inline_keyboard[0][0].text)

    first_response = next(telegram.iter_history(BOT_ID))

    assert first_response.text.find('Do you really want to restart the container') != -1, \
        "Not correct response after clicking on container button!"

    if confirm:
        first_response.click("YES ✅")
        time.sleep(3)
        second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
        second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))
        assert second_response_1.text.find("successfully restarted!") != -1, \
            "YES button on restart confirmation does not yield restart statement"
        assert second_response_2.text.find("You're in the Admin Area - proceed with care") != -1, \
            "YES button on restart confirmation does not go back to 🗝 ADMIN AREA"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text.find("second") != -1, \
            "YES button on restart confirmation does not restart container"
    else:
        first_response.click("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text.find("You're in the Admin Area - proceed with care") != -1, \
            "NO button on restart confirmation does not go back to 🗝 ADMIN AREA"
    print("Restart container with confirmation=" + str(confirm) + " ✅")
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
                   'Status: ' + node_data_original[0]['status'].capitalize()
        if field == 'status':
            expected_response += ' ➡️ ' + node_data_new[0]['status'].capitalize()
        expected_response += '\nBond: ' + tor_to_rune(node_data_original[0]['bond'])
        if field == 'bond':
            expected_response += ' ➡️ ' + tor_to_rune(node_data_new[0]['bond'])
        expected_response += '\nSlash Points: ' + '{:,}'.format(int(node_data_original[0]['slash_points']))
        if field == 'slash_points':
            expected_response += ' ➡️ ' + '{:,}'.format(int(node_data_new[0]['slash_points']))

    assert first_response.text.find(expected_response) != -1, \
        "Expected '" + expected_response + "' but got '" + first_response.text + "'"
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible after thornode value change notification."
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
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible after block height notification"

    time.sleep(70)
    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    expected_response = 'Block height is increasing again!'

    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible after block height notification"
    print("Check Blockchain Height ✅")
    print("------------------------")


def test_catch_up_notification(catching_up):
    with open('status.json') as json_read_file:
        node_data = json.load(json_read_file)

    node_data['result']['sync_info']['catching_up'] = catching_up

    with open('status.json', 'w') as json_write_file:
        json.dump(node_data, json_write_file)
    time.sleep(40)

    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    if catching_up:
        expected_response = 'The Node is behind the latest block height and catching up!'
    else:
        expected_response = 'The node caught up to the latest block height again!'
        
    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible after catching_up=" + catching_up + " notification"

    print("Check catch up status with catching_up=" + str(catching_up) + " ✅")
    print("------------------------")
    

def test_midgard_notification(healthy):
    assert_health_notification(THORCHAIN, healthy)

def test_binance_health_notification(healthy):
    assert_health_notification(BINANCE, healthy)


"""
######################################################################################################################################################
HELPER
######################################################################################################################################################
"""


def click_button(button):
    """
    Click a button and wait
    """

    response = next(telegram.iter_history(BOT_ID))
    response.click(button)
    time.sleep(3)


def tor_to_rune(tor_string):
    """
    1e8 Tor are 1 Rune
    """

    tor_int = int(tor_string)
    if tor_int >= 100000000:
        return "{:,} RUNE".format(int(tor_int / 100000000))
    else:
        return '{:.8f} RUNE'.format(tor_int / 100000000)


def assert_back_button(text):
    """
    Click back button and assert TG shows what was shown before
    """

    click_button("⬅️ BACK")

    response = next(telegram.iter_history(BOT_ID))

    assert response.text == text


def are_container_running():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("🗝 ADMIN AREA")

    response = next(telegram.iter_history(BOT_ID))

    if response.reply_markup.inline_keyboard[0][0].text == "⬅️ BACK":
        print("No container are running!")
        return False
    else:
        print("Container are running!")
        return True


def assert_health_notification(chain, healthy):
    if chain == THORCHAIN:
        file_name = "midgard"
        messageContent = "Midgard API"
    elif chain == BINANCE:
        file_name = "binance_health"
        messageContent = "Binance Node"
    else:
        assert False, "Chain in assert_health_notification is not recognized"

    if healthy:
        os.rename(file_name + '_404.json', file_name + '.json')
    else:
        os.rename(file_name + '.json', file_name + '_404.json')
    time.sleep(40)

    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    if healthy:
        expected_response = messageContent + ' is healthy again'
    else:
        expected_response = messageContent + ' is not healthy anymore'

    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible after block height notification"

    print("Check " + messageContent + " with healthy==" + str(healthy) + " ✅")
    print("------------------------")


"""
######################################################################################################################################################
TESTING COLLAGE
######################################################################################################################################################
"""


with telegram:
    try:
        time.sleep(5)
        test_start()

        # Test My Thornode Area
        test_my_thornodes()
        test_back_button_my_thornodes()

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
        test_back_button_thornode_details()

        test_delete_address(confirm=False)
        test_delete_address(confirm=True)

        test_add_all_addresses(confirm=False)
        test_add_all_addresses(confirm=True)

        test_delete_all_addresses(confirm=False)
        test_delete_all_addresses(confirm=True)

        test_add_address(address=VALID_ADDRESS,
                         expected_response1="What's the address of your THORNode? (enter /cancel to return to the menu)",
                         expected_response2="Got it! 👌")

        # Test Show all THORNodes Area
        test_show_all_thorchain_nodes()

        # Test Admin Area
        test_admin_area()
        test_back_button_admin_area()
        if are_container_running():
            test_restart_container(confirm=False)
            test_restart_container(confirm=True)

        test_thornode_notification(field="status")
        test_thornode_notification(field="bond")
        test_thornode_notification(field="slash_points")
        test_thornode_notification(field="node_address")
        test_block_height_notification()
        test_catch_up_notification(catching_up=True)
        test_catch_up_notification(catching_up=False)
        test_midgard_notification(healthy=False)
        test_midgard_notification(healthy=True)
        test_binance_health_notification(healthy=False)
        test_binance_health_notification(healthy=True)

        print("✅ -----ALL TESTS PASSED----- ✅")

    except AssertionError as e:
        print("💥 Assertion Error: 💥")
        print(e)
        print("💥 --> Shutting done Thornode Bot Process, Mock API Server Process and Telegram Client... 💥")
    finally:
        thornode_bot_process.terminate()
