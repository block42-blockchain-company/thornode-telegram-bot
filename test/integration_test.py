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
VALID_ADDRESS_TRUNCATED = VALID_ADDRESS[:9] + "..." + VALID_ADDRESS[-4:]

BOT_ID = os.environ['TELEGRAM_BOT_ID']

STATUS_EMOJIS = {"active": "💚", "standby": "📆", "disabled": "🔴"}

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
    assert response.reply_markup.keyboard[0][0] == "📡 MY NODES", "📡 MY NODES not visible after /start"
    assert response.reply_markup.keyboard[0][1] == "🌎 NETWORK", "🌎 NETWORK not visible after /start"
    assert response.reply_markup.keyboard[1][0] == "👀 SHOW ALL", "👀 SHOW ALL not visible after /start"
    assert response.reply_markup.keyboard[1][1] == "🔑 ADMIN AREA", "🔑 ADMIN AREA not visible after /start"
    print("/start ✅")
    print("------------------------")


def test_my_thornodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    assert response.reply_markup.inline_keyboard[0][0].text == "1️⃣ ADD NODE", "1️⃣ ADD NODE not visible after clicking on 📡 MY NODES"
    assert response.reply_markup.inline_keyboard[1][0].text == "➕ ADD ALL", "➕ ADD ALL not visible after clicking on 📡 MY NODES"
    assert response.reply_markup.inline_keyboard[1][1].text == "➖ REMOVE ALL", "➖ REMOVE ALL not visible after clicking on 📡 MY NODES"
    print("📡 MY NODES ✅")
    print("------------------------")


def test_add_address(address, expected_response1, expected_response2):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)

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
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    click_button(response.reply_markup.inline_keyboard[0][0].text)

    response = next(telegram.iter_history(BOT_ID))

    number_of_unconfirmed_txs = json.load(open('unconfirmed_txs.json'))['result']['total']

    assert response.text.find("Address: " + VALID_ADDRESS) != -1, "Thornode Details not showing stats"
    assert response.text.find("Number of Unconfirmed Txs: " + number_of_unconfirmed_txs) != -1, \
        "Thornode Details not showing Number of unconfirmed Txs"
    assert response.reply_markup.inline_keyboard[0][0].text == "➖ REMOVE", \
        "➖ REMOVE Button not in Thornode Details"
    assert response.reply_markup.inline_keyboard[0][1].text == "✏️ CHANGE ALIAS", \
        "✏️ CHANGE ALIAS Button not in Thornode Details"
    assert response.reply_markup.inline_keyboard[1][0].text == "⬅️ BACK", "⬅️ BACK Show Button not in Thornode Details"

    print("Thornode Details with " + VALID_ADDRESS + " ✅")
    print("------------------------")


def test_back_button_thornode_details():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    click_button(response.reply_markup.inline_keyboard[0][0].text)

    assert_back_button(response.text)

    print("Back button in Thornode Details ✅")
    print("------------------------")


def test_delete_address(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)
    response = next(telegram.iter_history(BOT_ID))
    click_button(response.reply_markup.inline_keyboard[0][0].text)

    click_button("➖ REMOVE")

    first_response = next(telegram.iter_history(BOT_ID))

    assert first_response.text.find('Do you really want to remove this node from your monitoring list?') != -1 and \
        first_response.text.find(VALID_ADDRESS) != -1, \
        "➖ REMOVE button doesn't work!"

    if confirm:
        click_button("YES ✅")
        time.sleep(3)
        second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
        second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))
        assert second_response_1.text.find("❌ Thornode got deleted! ❌\n") != -1 and \
               second_response_1.text.find(VALID_ADDRESS) != -1, \
            "YES button on deletion confirmation does not yield deletion statement"
        assert second_response_2.text == "Click an address from the list below or add a node:", \
            "YES button on deletion confirmation does not go back to thornodes menu"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text == "1️⃣ ADD NODE", "Node is NOT deleted after deletion"
    else:
        click_button("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text.find("Address: " + VALID_ADDRESS) != -1, \
            "NO button on single address deletion confirmation does not go back to Thornode details"
    print("➖ REMOVE Address with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_change_alias(alias, expected_response1, expected_response2):
    pass

    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    click_button(response.reply_markup.inline_keyboard[0][0].text)

    click_button("✏️ CHANGE ALIAS")

    first_response = next(telegram.iter_history(BOT_ID))
    telegram.send_message(BOT_ID, alias)
    time.sleep(3)
    second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    assert first_response.text == expected_response1, "Expected '" + expected_response1 + "' but got '" + first_response.text + "'"
    assert second_response_1.text == expected_response2 or second_response_2.text == expected_response2, \
        "Expected '" + expected_response2 + "' but got '" + second_response_1.text + "' and '" + second_response_2.text + "'"
    print("✏️ CHANGE ALIAS with " + alias + " ✅")
    print("------------------------")


def test_add_all_addresses(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)
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
        assert second_response_2.text == "Click an address from the list below or add a node:", \
            "YES button on ➕ ADD ALL confirmation does not go back to 📡 MY NODES menu"
        assert second_response_2.reply_markup.inline_keyboard[1][0].text.find('thor') != -1,\
            "Nodes are not added after YES button on ➕ ADD ALL confirmation"
    else:
        click_button("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text == "Click an address from the list below or add a node:", \
            "NO button on ➕ ADD ALL confirmation does not go back to 📡 MY NODES menu"

    print("➕ ADD ALL with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_delete_all_addresses(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "📡 MY NODES")
    time.sleep(3)
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
        assert second_response_2.text == "Click an address from the list below or add a node:", \
            "YES button on ➖ REMOVE ALL confirmation does not go back to 📡 MY NODES menu"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text == '1️⃣ ADD NODE' and \
            "Nodes are not deleted after YES button on ➖ REMOVE ALL confirmation"
    else:
        click_button("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text == "Click an address from the list below or add a node:", \
            "NO button on ➖ REMOVE ALL confirmation does not go back to 📡 MY NODES menu"

    print("➖ REMOVE ALL with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_network():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    telegram.send_message(BOT_ID, "🌎 NETWORK")

    time.sleep(10)
    response = next(telegram.iter_history(BOT_ID))

    expected_response1 = 'Status of the whole THORChain network:'
    expected_response2 = 'Network Security:'
    assert response.text.find(expected_response1) != -1, "Expected '" + expected_response1 + \
                                                         "'\nbut got\n'" + response.text + "'"
    assert response.text.find(expected_response2) != -1, "Expected '" + expected_response2 + \
                                                         "'\nbut got\n'" + response.text + "'"

    print("🌎 NETWORK ✅")
    print("------------------------")


def test_show_all_thorchain_nodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    telegram.send_message(BOT_ID, "👀 SHOW ALL")

    time.sleep(3)
    response = next(telegram.iter_history(BOT_ID))

    expected_response1 = 'Status of all THORNodes in the THORChain network:'
    expected_response2 = 'Address: ' + VALID_ADDRESS
    assert response.text.find(expected_response1) != -1, "Expected '" + expected_response1 + \
                                                              "'\nbut got\n'" + response.text + "'"
    assert response.text.find(expected_response2) != -1, "Expected '" + expected_response2 + \
                                                               "'\nbut got\n'" + response.text + "'"
    print("👀 SHOW ALL ✅")
    print("------------------------")


def test_admin_area():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    telegram.send_message(BOT_ID, "🔑 ADMIN AREA")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))

    assert response.text.find("You're in the Admin Area - proceed with care") != -1, \
        "🔑 ADMIN AREA Message not visible after clicking on 🔑 ADMIN AREA"

    print("🔑 ADMIN AREA ✅")
    print("------------------------")


def test_back_button_admin_area():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    telegram.send_message(BOT_ID, "🔑 ADMIN AREA")
    time.sleep(3)

    print("Back button in 🔑 ADMIN AREA ✅")
    print("------------------------")


def test_restart_container(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    telegram.send_message(BOT_ID, "🔑 ADMIN AREA")
    time.sleep(3)
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
            "YES button on restart confirmation does not go back to 🔑 ADMIN AREA"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text.find("second") != -1, \
            "YES button on restart confirmation does not restart container"
    else:
        first_response.click("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text.find("You're in the Admin Area - proceed with care") != -1, \
            "NO button on restart confirmation does not go back to 🔑 ADMIN AREA"
    print("Restart container with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_thornode_notification(field):
    with open('nodeaccounts.json') as json_read_file:
        node_data_original = json.load(json_read_file)
        node_data_new = copy.deepcopy(node_data_original)

    new_value = random.randrange(0, 100)
    if field == 'node_address':
        new_value = 'thor' + str(new_value)
    elif field == 'status':
        statuses = ['active', 'standby', 'disabled']
        if statuses[new_value % 3] == node_data_original[0][field]:
            new_value += 1
        new_value = statuses[new_value % 3]
    else:
        new_value += int(node_data_new[0][field])

    node_data_new[0][field] = str(new_value)

    with open('nodeaccounts.json', 'w') as json_write_file:
        json.dump(node_data_new, json_write_file)

    time.sleep(70)
    response = next(telegram.iter_history(BOT_ID))

    if field == "node_address":
        expected_response = 'THORNode Thor-1 is not active anymore! 💀' + '\n' + \
                           'Address: ' + node_data_original[0]['node_address'] + '\n\n' + \
                           'Please enter another THORNode address.'
    else:
        expected_response = 'THORNode: ' + 'Thor-1' + '\n' + \
                            'Address: ' + node_data_original[0]['node_address'] + '\n' + \
                            'Status: ' + node_data_original[0]['status'].capitalize()
        if field == 'status':
            expected_response += ' ➡️ ' + node_data_new[0]['status'].capitalize()
        expected_response += '\nBond: ' + tor_to_rune(node_data_original[0]['bond'])
        if field == 'bond':
            expected_response += ' ➡️ ' + tor_to_rune(node_data_new[0]['bond'])
        expected_response += '\nSlash Points: ' + '{:,}'.format(int(node_data_original[0]['slash_points']))
        if field == 'slash_points':
            expected_response += ' ➡️ ' + '{:,}'.format(int(node_data_new[0]['slash_points']))

    assert response.text.find(expected_response) != -1, \
        "Expected '" + expected_response + "' but got '" + response.text + "'"
    print("Notification Thornode data change with " + field + " ✅")
    print("------------------------")
    time.sleep(50)


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

    response = next(telegram.iter_history(BOT_ID))

    expected_response = 'Block height is not increasing anymore!'
    assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + response.text + "'"

    time.sleep(70)
    response = next(telegram.iter_history(BOT_ID))

    expected_response = 'Block height is increasing again!'
    assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + response.text + "'"
    print("Check Blockchain Height ✅")
    print("------------------------")


def test_catch_up_notification(catching_up):
    with open('status.json') as json_read_file:
        node_data = json.load(json_read_file)

    node_data['result']['sync_info']['catching_up'] = catching_up

    with open('status.json', 'w') as json_write_file:
        json.dump(node_data, json_write_file)
    time.sleep(40)

    response = next(telegram.iter_history(BOT_ID))

    if catching_up:
        expected_response = 'The Node is behind the latest block height and catching up!'
    else:
        expected_response = 'The node caught up to the latest block height again!'
        
    assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + response.text + "'"

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
    telegram.send_message(BOT_ID, "🔑 ADMIN AREA")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))

    if response.reply_markup.inline_keyboard[0][0]:
        print("Container are running!")
        return True
    else:
        print("No container are running!")
        return False


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

    response = next(telegram.iter_history(BOT_ID))

    if healthy:
        expected_response = messageContent + ' is healthy again'
    else:
        expected_response = messageContent + ' is not healthy anymore'

    assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + response.text + "'"

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

        test_add_address(address="invalidAddress",
                         expected_response1="What's the address of your THORNode?",
                         expected_response2="⛔️ I have not found a THORNode with this address! Please try another one.")
        test_add_address(address=VALID_ADDRESS,
                         expected_response1="What's the address of your THORNode?",
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
                         expected_response1="What's the address of your THORNode?",
                         expected_response2="Got it! 👌")

        test_change_alias(alias="SomeNewAliasThatIsUnfortunatelyTooLong",
                          expected_response1='How would you like to name your THORNode?',
                          expected_response2="⛔️ Alias cannot have more than 16 characters! Please try another one.")
        test_change_alias(alias="newAlias",
                          expected_response1='How would you like to name your THORNode?',
                          expected_response2="Got it! 👌")

        test_delete_all_addresses(True)

        # Test Show all THORNodes Area
        test_show_all_thorchain_nodes()

        # Test Network View
        test_network()

        # Test Admin Area
        test_admin_area()
        test_back_button_admin_area()
        if are_container_running():
            test_restart_container(confirm=False)
            test_restart_container(confirm=True)

        test_add_address(address=VALID_ADDRESS,
                         expected_response1="What's the address of your THORNode?",
                         expected_response2="Got it! 👌")

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
