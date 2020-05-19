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

"""
######################################################################################################################################################
TEST CASES
######################################################################################################################################################
"""


def test_start():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    assert response.reply_markup.inline_keyboard[0][0].text == "My THORNodes", "My THORNodes not visible after /start"
    assert response.reply_markup.inline_keyboard[0][1].text == "Admin Area", "Admin Area not visible after /start"
    print("/start ✅")
    print("------------------------")


def test_my_thornodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    click_button("My THORNodes")

    response = next(telegram.iter_history(BOT_ID))
    assert response.reply_markup.inline_keyboard[0][0].text == "Add THORNode", "Add THORNode not visible after clicking on My THORNodes"
    assert response.reply_markup.inline_keyboard[0][1].text == "<< Back", "<< Back not visible after clicking on My THORNodes"
    print("My THORNodes ✅")
    print("------------------------")


def test_back_button_my_thornodes():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    response = next(telegram.iter_history(BOT_ID))
    click_button("My THORNodes")

    assert_back_button(response.text)

    print("Back button in My THORNodes ✅")
    print("------------------------")


def test_add_address(address, expected_response1, expected_response2):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("My THORNodes")

    click_button("Add THORNode")

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
    click_button("My THORNodes")
    
    click_button(VALID_ADDRESS)

    response = next(telegram.iter_history(BOT_ID))

    assert response.text.find("THORNode: " + VALID_ADDRESS) != -1, \
        "Thornode Details not showing stats"
    assert response.reply_markup.inline_keyboard[0][0].text == "Delete THORNode", "Delete THORNode Button not in Thornode Details"
    assert response.reply_markup.inline_keyboard[0][1].text == "<< Back", "<< Back Show Button not in Thornode Details"

    print("Thornode Details with " + VALID_ADDRESS + " ✅")
    print("------------------------")


def test_back_button_thornode_details():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("My THORNodes")

    response = next(telegram.iter_history(BOT_ID))

    click_button(VALID_ADDRESS)
    assert_back_button(response.text)

    print("Back button in Thornode Details ✅")
    print("------------------------")


def test_delete_address(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("My THORNodes")
    click_button(VALID_ADDRESS)

    click_button("Delete THORNode")

    first_response = next(telegram.iter_history(BOT_ID))

    assert first_response.text == '⚠️ Do you really want to remove the address from your monitoring list? ⚠️\n' + VALID_ADDRESS, \
        "Delete THORNode button doesn't work!"

    if confirm:
        first_response.click("YES ✅")
        time.sleep(3)
        second_response_1 = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
        second_response_2 = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))
        assert second_response_1.text == "❌ Thornode address got deleted! ❌\n" + VALID_ADDRESS, \
            "YES button on deletion confirmation does not yield deletion statement"
        assert second_response_2.text == "Choose an address from the list below or add one:", \
            "YES button on deletion confirmation does not go back to thornodes menu"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text == "Add THORNode", "Node is NOT deleted after deletion"
    else:
        first_response.click("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text.find("THORNode: " + VALID_ADDRESS) != -1, \
            "NO button on deletion confirmation does not go back to Thornode details"
    print("Delete Address with confirmation=" + str(confirm) + " ✅")
    print("------------------------")


def test_admin_area():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    click_button("Admin Area")

    response = next(telegram.iter_history(BOT_ID))

    back_button_found = False
    for button in response.reply_markup.inline_keyboard:
        back_button_found = True if button[0].text == "<< Back" else False

    assert response.text.find("You're in the Admin Area - proceed with care") != -1, \
        "Admin Area Message not visible after clicking on Admin Area"
    assert back_button_found, "<< Back not visible after clicking on Admin Area"

    print("Admin Area ✅")
    print("------------------------")


def test_back_button_admin_area():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)

    response = next(telegram.iter_history(BOT_ID))
    click_button("Admin Area")

    assert_back_button(response.text)

    print("Back button in Admin Area ✅")
    print("------------------------")


def test_restart_container(confirm):
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("Admin Area")
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
            "YES button on restart confirmation does not go back to Admin Area"
        assert second_response_2.reply_markup.inline_keyboard[0][0].text.find("second") != -1, \
            "YES button on restart confirmation does not restart container"
    else:
        first_response.click("NO ❌")
        time.sleep(3)
        second_response = next(telegram.iter_history(BOT_ID))
        assert second_response.text.find("You're in the Admin Area - proceed with care") != -1, \
            "NO button on restart confirmation does not go back to Admin Area"
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
    

def test_midgard_notification(health_status):
    with open('midgard.json', 'w') as write_file:
        write_file.write(health_status)
    time.sleep(40)
    
    first_response = next(itertools.islice(telegram.iter_history(BOT_ID), 1, None))
    second_response = next(itertools.islice(telegram.iter_history(BOT_ID), 0, None))

    if health_status == '"FAIL"':
        expected_response = 'Midgard API is not healthy anymore'
    elif health_status == '"OK"':
        expected_response = 'Midgard API is healthy again'
    else:
        assert False, 'Health status for Midgard API test is neither "FAIL" nor "OK"'
        
    assert first_response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                              "'\nbut got\n'" + first_response.text + "'"
    assert second_response.text == "I am your THORNode Bot. 🤖\nChoose an action:", \
        "I am your THORNode Bot. 🤖\nChoose an action: - not visible after block height notification"

    print("Check Midgard API with health_status=" + health_status + " ✅")
    print("------------------------")


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

    click_button("<< Back")

    response = next(telegram.iter_history(BOT_ID))

    assert response.text == text


def are_container_running():
    telegram.send_message(BOT_ID, "/start")
    time.sleep(3)
    click_button("Admin Area")

    response = next(telegram.iter_history(BOT_ID))

    if response.reply_markup.inline_keyboard[0][0].text == "<< Back":
        print("No container are running!")
        return False
    else:
        print("Container are running!")
        return True


"""
######################################################################################################################################################
TESTING COLLAGE
######################################################################################################################################################
"""


with telegram:
    try:
        time.sleep(5)
        test_start()
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
        test_add_address(address=VALID_ADDRESS,
                         expected_response1="What's the address of your THORNode? (enter /cancel to return to the menu)",
                         expected_response2="Got it! 👌")

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
        test_midgard_notification(health_status='"FAIL"')
        test_midgard_notification(health_status='"OK"')

        print("✅ -----ALL TESTS PASSED----- ✅")

    except AssertionError as e:
        print("💥 Assertion Error: 💥")
        print(e)
        print("💥 --> Shutting done Thornode Bot Process, Mock API Server Process and Telegram Client... 💥")
    finally:
        thornode_bot_process.terminate()
