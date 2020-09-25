import copy
import json
import time
import os
import itertools
import random
import unittest
import sys

from bot.helpers import tor_to_rune

sys.path.append('..')

from subprocess import Popen
from pyrogram import Client as TelegramClient

"""
######################################################################################################################################################
Static & environment variables
######################################################################################################################################################
"""

STATUS_EMOJIS = {"active": "💚", "standby": "📆", "disabled": "🔴"}

THORCHAIN, BINANCE = range(2)

"""
######################################################################################################################################################
TEST CASES
######################################################################################################################################################
"""


class ThornodeBot(unittest.TestCase):
    thornode_bot_process = None
    telegram = None
    BOT_ID = os.environ['TELEGRAM_BOT_ID']

    @classmethod
    def setUpClass(cls):
        # Delete previous sessions for clean testing
        if os.path.exists("../storage/session.data"):
            os.remove("../storage/session.data")

        # Authenticate Telegram Client of this testing suite
        try:
            with open('telegram_session.string', 'r') as read_file:
                telegram_session_string = read_file.read().splitlines()[0]
        except FileNotFoundError:
            assert False, "File 'telegram_session.string' was not found!\n" \
                          "Please run first 'python3 sign_in_telegram.py' to create 'telegram_session.string'!"

        cls.telegram = TelegramClient(
            telegram_session_string,
            api_id=os.environ['TELEGRAM_API_ID'],
            api_hash=os.environ['TELEGRAM_API_HASH']
        )

        # Start the Telegram Terra Node Bot
        cls.thornode_bot_process = Popen(['python3', 'bot/thornode_bot.py'], cwd="../")
        time.sleep(5)

        with cls.telegram:
            cls.telegram.send_message(cls.BOT_ID, "/start")
            time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.thornode_bot_process.terminate()

    def test_start(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(7)

            response = next(self.telegram.iter_history(self.BOT_ID))
            assert response.reply_markup.keyboard[0][0] == "📡 MY NODES", "📡 MY NODES not visible after /start"
            assert response.reply_markup.keyboard[0][1] == "🌎 NETWORK", "🌎 NETWORK not visible after /start"
            assert response.reply_markup.keyboard[1][0] == "👀 SHOW ALL", "👀 SHOW ALL not visible after /start"
            assert response.reply_markup.keyboard[1][1] == "🔑 ADMIN AREA", "🔑 ADMIN AREA not visible after /start"
            print("/start ✅")
            print("------------------------")

    def test_my_thornodes(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)

            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)

            response = next(self.telegram.iter_history(self.BOT_ID))
            inline_keyboard_len = len(response.reply_markup.inline_keyboard)
            assert response.reply_markup.inline_keyboard[inline_keyboard_len - 2][0].text == "1️⃣ ADD NODE", "1️⃣ ADD NODE not visible after clicking on 📡 MY NODES"
            assert response.reply_markup.inline_keyboard[inline_keyboard_len - 1][0].text == "➕ ADD ALL", "➕ ADD ALL not visible after clicking on 📡 MY NODES"
            assert response.reply_markup.inline_keyboard[inline_keyboard_len - 1][1].text == "➖ REMOVE ALL", "➖ REMOVE ALL not visible after clicking on 📡 MY NODES"
            print("📡 MY NODES ✅")
            print("------------------------")

    def test_add_address_invalid(self):
        self.assert_add_address(address="invalidAddress",
                     expected_response1="What's the address of your THORNode?",
                     expected_response2="⛔️ I have not found a THORNode with this address! Please try another one.")

    def test_add_address_valid(self):
        self.add_valid_address()

    def test_thornode_detail(self):
        valid_address = self.add_valid_address()

        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)

            response = next(self.telegram.iter_history(self.BOT_ID))
            self.click_button(response.reply_markup.inline_keyboard[0][0].text)
            time.sleep(15)

            response = next(self.telegram.iter_history(self.BOT_ID))

            number_of_unconfirmed_txs = json.load(open('mock_files/unconfirmed_txs.json'))['result']['total']

            assert response.text.find("Address: " + valid_address) != -1, "Thornode Details not showing stats"
            assert response.text.find("Number of Unconfirmed Transactions: " + number_of_unconfirmed_txs) != -1, \
                "Thornode Details not showing Number of unconfirmed Transactions"
            assert response.reply_markup.inline_keyboard[0][0].text == "➖ REMOVE", \
                "➖ REMOVE Button not in Thornode Details"
            assert response.reply_markup.inline_keyboard[0][1].text == "✏️ CHANGE ALIAS", \
                "✏️ CHANGE ALIAS Button not in Thornode Details"
            assert response.reply_markup.inline_keyboard[1][0].text == "⬅️ BACK", "⬅️ BACK Show Button not in Thornode Details"

            print("Thornode Details with " + valid_address + " ✅")
            print("------------------------")

    def test_back_button_thornode_details(self):
        self.add_valid_address()

        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)

            response = next(self.telegram.iter_history(self.BOT_ID))
            self.click_button(response.reply_markup.inline_keyboard[0][0].text)
            time.sleep(5)

            self.assert_back_button(response.text)

            print("Back button in Thornode Details ✅")
            print("------------------------")

    def test_delete_address_confirm_false(self):
        self.assert_delete_address(confirm=False)

    def test_delete_address_confirm_true(self):
        self.assert_delete_address(confirm=True)

    def test_change_alias_invalid(self):
        self.assert_change_alias(alias="SomeNewAliasThatIsUnfortunatelyTooLong",
                              expected_response1='How would you like to name your THORNode?',
                              expected_response2="⛔️ Alias cannot have more than 16 characters! Please try another one.")

    def test_change_alias_valid(self):
        self.assert_change_alias(alias="newAlias",
                              expected_response1='How would you like to name your THORNode?',
                              expected_response2="Got it! 👌")

    def test_add_all_addresses_confirm_false(self):
        self.assert_add_all_addresses(confirm=False)

    def test_add_all_addresses_confirm_true(self):
        self.assert_add_all_addresses(confirm=True)
        self.assert_delete_all_addresses(confirm=True)

    def test_delete_all_addresses_confirm_false(self):
        self.assert_delete_all_addresses(confirm=False)

    def test_delete_all_addresses_confirm_true(self):
        self.assert_delete_all_addresses(confirm=True)

    def test_network(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)

            self.telegram.send_message(self.BOT_ID, "🌎 NETWORK")
            time.sleep(3)
            self.click_button("📊 NETWORK STATS")

            time.sleep(15)
            response = next(self.telegram.iter_history(self.BOT_ID))

            expected_response1 = 'Status of the whole THORChain network:'
            expected_response2 = 'Network Security:'
            assert response.text.find(expected_response1) != -1, "Expected '" + expected_response1 + \
                                                                 "'\nbut got\n'" + response.text + "'"
            assert response.text.find(expected_response2) != -1, "Expected '" + expected_response2 + \
                                                                 "'\nbut got\n'" + response.text + "'"

            print("🌎 NETWORK ✅")
            print("------------------------")

    def test_show_all_thorchain_nodes(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)

            self.telegram.send_message(self.BOT_ID, "👀 SHOW ALL")

            time.sleep(7)
            response = next(self.telegram.iter_history(self.BOT_ID))

            expected_response = 'THORNode: not monitored'
            assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                                      "'\nbut got\n'" + response.text + "'"
            print("👀 SHOW ALL ✅")
            print("------------------------")

    def test_admin_area(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)

            self.telegram.send_message(self.BOT_ID, "🔑 ADMIN AREA")
            time.sleep(3)

            response = next(self.telegram.iter_history(self.BOT_ID))

            assert response.text.find("You're in the Admin Area - proceed with care") != -1, \
                "🔑 ADMIN AREA Message not visible after clicking on 🔑 ADMIN AREA"

            print("🔑 ADMIN AREA ✅")
            print("------------------------")

    def test_restart_container(self):
        if self.are_container_running():
            self.assert_restart_container(confirm=False)
            self.assert_restart_container(confirm=True)

    def test_back_button_admin_area(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)

            self.telegram.send_message(self.BOT_ID, "🔑 ADMIN AREA")
            time.sleep(3)

            print("Back button in 🔑 ADMIN AREA ✅")
            print("------------------------")

    def test_block_height_notification(self):
        self.add_valid_address()
        with self.telegram:
            with open('mock_files/status.json') as json_read_file:
                node_data = json.load(json_read_file)

            block_height = node_data['result']['sync_info']['latest_block_height']
            new_block_height = int(block_height) - 200
            node_data['result']['sync_info']['latest_block_height'] = str(new_block_height)

            time.sleep(7)
            with open('mock_files/status.json', 'w') as json_write_file:
                json.dump(node_data, json_write_file)
            time.sleep(5)

            response = next(self.telegram.iter_history(self.BOT_ID))

            expected_response = 'Block height is not increasing anymore!'
            assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                                "'\nbut got\n'" + response.text + "'"

            time.sleep(12)
            response = next(self.telegram.iter_history(self.BOT_ID))

            expected_response = 'Block height is increasing again!'
            assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                                "'\nbut got\n'" + response.text + "'"
            print("Check Blockchain Height ✅")
            print("------------------------")

    def test_node_version_notification(self):
        self.add_valid_address()
        with self.telegram:
            with open('mock_files/nodeaccounts.json') as json_read_file:
                node_data = json.load(json_read_file)

            a, b, c = str(node_data[0]['version']).split('.')
            node_data[0]['version'] = a + '.' + b + '.' + str(int(c) + 1)

            with open('mock_files/nodeaccounts.json', 'w') as json_write_file:
                json.dump(node_data, json_write_file)

            time.sleep(12)

            response = next(self.telegram.iter_history(self.BOT_ID))

            expected_response = 'Consider updating the software on your node:'
            assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                                "'\nbut got\n'" + response.text + "'"

    def test_thornode_notification_status(self):
        self.assert_thornode_notification_status()

    def test_thornode_notification_bond(self):
        self.assert_thornode_notification(field="bond")

    def test_thornode_notification_slash_points(self):
        self.assert_thornode_notification(field="slash_points")

    def test_thornode_notification_node_address(self):
        self.assert_thornode_notification(field="node_address")

    def test_catch_up_notification(self):
        self.add_valid_address()
        self.assert_catch_up_notification(catching_up=True)
        self.assert_catch_up_notification(catching_up=False)

    def test_midgard_notification(self):
        self.add_valid_address()
        self.assert_health_notification(THORCHAIN, healthy=False)
        self.assert_health_notification(THORCHAIN, healthy=True)

    def test_binance_health_notification(self):
        self.add_valid_address()
        self.assert_health_notification(BINANCE, healthy=False)
        self.assert_health_notification(BINANCE, healthy=True)


    """
    ######################################################################################################################################################
    HELPER
    ######################################################################################################################################################
    """

    def click_button(self, button):
        """
        Click a button and wait
        """

        response = next(self.telegram.iter_history(self.BOT_ID))
        response.click(button)
        time.sleep(3)

    def assert_back_button(self, text):
        """
        Click back button and assert TG shows what was shown before
        """

        self.click_button("⬅️ BACK")

        response = next(self.telegram.iter_history(self.BOT_ID))

        assert response.text == text

    def add_valid_address(self):
        valid_address = json.load(open('mock_files/nodeaccounts.json'))[0]['node_address']
        self.assert_add_address(address=valid_address,
                     expected_response1="What's the address of your THORNode?",
                     expected_response2="Got it! 👌")
        return valid_address

    def are_container_running(self):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "🔑 ADMIN AREA")
            time.sleep(3)

            response = next(self.telegram.iter_history(self.BOT_ID))

            if response.reply_markup.inline_keyboard[0][0]:
                print("Container are running!")
                return True
            else:
                print("No container are running!")
                return False

    def assert_health_notification(self, chain, healthy):
        with self.telegram:
            if chain == THORCHAIN:
                file_name = "mock_files/midgard"
                messageContent = "Midgard API"
            elif chain == BINANCE:
                file_name = "mock_files/binance_health"
                messageContent = "Binance Node"
            else:
                assert False, "Chain in assert_health_notification is not recognized"

            if healthy:
                os.rename(file_name + '_404.json', file_name + '.json')
            else:
                os.rename(file_name + '.json', file_name + '_404.json')
            time.sleep(7)

            response = next(self.telegram.iter_history(self.BOT_ID))

            if healthy:
                expected_response = messageContent + ' is healthy again'
            else:
                expected_response = messageContent + ' is not healthy anymore'

            assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                                      "'\nbut got\n'" + response.text + "'"

            print("Check " + messageContent + " with healthy==" + str(healthy) + " ✅")
            print("------------------------")

    def assert_add_address(self, address, expected_response1, expected_response2):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)

            self.click_button("1️⃣ ADD NODE")

            first_response = next(self.telegram.iter_history(self.BOT_ID))
            self.telegram.send_message(self.BOT_ID, address)
            time.sleep(5)
            second_response_1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
            second_response_2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))

            assert first_response.text == expected_response1, "Expected '" + expected_response1 + "' but got '" + first_response.text + "'"
            assert second_response_1.text == expected_response2 or second_response_2.text == expected_response2, \
                "Expected '" + expected_response2 + "' but got '" + second_response_1.text + "' and '" + second_response_2.text + "'"
            print("1️⃣ ADD NODE with " + address + " ✅")
            print("------------------------")

    def assert_add_all_addresses(self, confirm):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)
            self.click_button("➕ ADD ALL")

            first_response = next(self.telegram.iter_history(self.BOT_ID))

            assert first_response.text == '⚠️ Do you really want to add all available THORNodes to your monitoring list? ⚠️', \
                "➕ ADD ALL button does not work!"

            if confirm:
                self.click_button("YES ✅")
                second_response_1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
                second_response_2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))
                assert second_response_1.text == "Added all THORNodes! 👌", \
                    "YES button on ➕ ADD ALL confirmation does not yield addition statement"
                assert second_response_2.text == "Click an address from the list below or add a node:", \
                    "YES button on ➕ ADD ALL confirmation does not go back to 📡 MY NODES menu"
                assert second_response_2.reply_markup.inline_keyboard[1][0].text.find('thor') != -1,\
                    "Nodes are not added after YES button on ➕ ADD ALL confirmation"
            else:
                self.click_button("NO ❌")
                time.sleep(3)
                second_response = next(self.telegram.iter_history(self.BOT_ID))
                assert second_response.text == "Click an address from the list below or add a node:", \
                    "NO button on ➕ ADD ALL confirmation does not go back to 📡 MY NODES menu"

            print("➕ ADD ALL with confirmation=" + str(confirm) + " ✅")
            print("------------------------")

    def assert_restart_container(self, confirm):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "🔑 ADMIN AREA")
            time.sleep(3)
            setup_response = next(self.telegram.iter_history(self.BOT_ID))

            self.click_button(setup_response.reply_markup.inline_keyboard[0][0].text)

            first_response = next(self.telegram.iter_history(self.BOT_ID))

            assert first_response.text.find('Do you really want to restart the container') != -1, \
                "Not correct response after clicking on container button!"

            if confirm:
                first_response.click("YES ✅")
                time.sleep(3)
                second_response_1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
                second_response_2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))
                assert second_response_1.text.find("successfully restarted!") != -1, \
                    "YES button on restart confirmation does not yield restart statement"
                assert second_response_2.text.find("You're in the Admin Area - proceed with care") != -1, \
                    "YES button on restart confirmation does not go back to 🔑 ADMIN AREA"
                assert second_response_2.reply_markup.inline_keyboard[0][0].text.find("second") != -1, \
                    "YES button on restart confirmation does not restart container"
            else:
                first_response.click("NO ❌")
                time.sleep(3)
                second_response = next(self.telegram.iter_history(self.BOT_ID))
                assert second_response.text.find("You're in the Admin Area - proceed with care") != -1, \
                    "NO button on restart confirmation does not go back to 🔑 ADMIN AREA"
            print("Restart container with confirmation=" + str(confirm) + " ✅")
            print("------------------------")

    def assert_change_alias(self, alias, expected_response1, expected_response2):
        self.add_valid_address()

        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)

            response = next(self.telegram.iter_history(self.BOT_ID))
            self.click_button(response.reply_markup.inline_keyboard[0][0].text)
            time.sleep(5)

            self.click_button("✏️ CHANGE ALIAS")

            first_response = next(self.telegram.iter_history(self.BOT_ID))
            self.telegram.send_message(self.BOT_ID, alias)
            time.sleep(3)
            second_response_1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
            second_response_2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))

            assert first_response.text == expected_response1, "Expected '" + expected_response1 + "' but got '" + first_response.text + "'"
            assert second_response_1.text == expected_response2 or second_response_2.text == expected_response2, \
                "Expected '" + expected_response2 + "' but got '" + second_response_1.text + "' and '" + second_response_2.text + "'"
            print("✏️ CHANGE ALIAS with " + alias + " ✅")
            print("------------------------")

    def assert_thornode_notification(self, field):
        self.add_valid_address()

        with self.telegram:
            with open('mock_files/nodeaccounts.json') as json_read_file:
                node_data_original = json.load(json_read_file)
                node_data_new = copy.deepcopy(node_data_original)

            new_value = random.randrange(0, 100)
            if field == 'node_address':
                new_value = 'thor' + str(new_value)
            else:
                new_value += int(node_data_new[0][field])

            node_data_new[0][field] = str(new_value)

            with open('mock_files/nodeaccounts.json', 'w') as json_write_file:
                json.dump(node_data_new, json_write_file)

            time.sleep(15)
            response = next(self.telegram.iter_history(self.BOT_ID))

            if field == "node_address":
                expected_response = 'is not active anymore! 💀' + '\n' + \
                                   'Address: ' + node_data_original[0]['node_address'] + '\n\n' + \
                                   'Please enter another THORNode address.'
            else:
                expected_response = 'Address: ' + node_data_original[0]['node_address'] + '\n' + \
                                    'Status: ' + node_data_original[0]['status'].capitalize()
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
            time.sleep(9)

    def assert_thornode_notification_status(self):
        self.add_valid_address()

        with self.telegram:
            with open('mock_files/nodeaccounts.json') as json_read_file:
                node_data_original = json.load(json_read_file)
                node_data_new = copy.deepcopy(node_data_original)

            if node_data_original[0]['status'] == 'active':
                node_data_new[0]['status'] = 'standby'
            else:
                node_data_new[0]['status'] = 'active'

            with open('mock_files/nodeaccounts.json', 'w') as json_write_file:
                json.dump(node_data_new, json_write_file)

            time.sleep(15)
            response1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
            response2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))

            expected_response1 = 'Address: ' + node_data_original[0]['node_address'] + '\n' + \
                                'Status: ' + node_data_original[0]['status'].capitalize()
            expected_response1 += ' ➡️ ' + node_data_new[0]['status'].capitalize()
            expected_response1 += '\nBond: ' + tor_to_rune(node_data_original[0]['bond'])
            expected_response1 += '\nSlash Points: ' + '{:,}'.format(int(node_data_original[0]['slash_points']))

            expected_response2 = "🔄 CHURN SUMMARY"

            assert response1.text.find(expected_response1) != -1 or response2.text.find(expected_response1) != -1, \
                "Expected '" + expected_response1 + "' but got '" + response1.text + "' and '" + response2.text + "'"
            assert response1.text.find(expected_response2) != -1 or response2.text.find(expected_response2) != -1, \
                "Expected '" + expected_response2 + "' but got '" + response1.text + "' and '" + response2.text + "'"
            print("Notification Thornode data change with status ✅")
            print("------------------------")
            time.sleep(9)

    def assert_delete_address(self, confirm):
        valid_address = self.add_valid_address()

        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)
            response = next(self.telegram.iter_history(self.BOT_ID))
            self.click_button(response.reply_markup.inline_keyboard[0][0].text)
            time.sleep(5)

            self.click_button("➖ REMOVE")

            first_response = next(self.telegram.iter_history(self.BOT_ID))

            assert first_response.text.find('Do you really want to remove this node from your monitoring list?') != -1 and \
                first_response.text.find(valid_address) != -1, \
                "➖ REMOVE button doesn't work!"

            if confirm:
                self.click_button("YES ✅")
                time.sleep(3)
                second_response_1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
                second_response_2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))
                assert second_response_1.text.find("❌ Thornode got deleted! ❌\n") != -1 and \
                       second_response_1.text.find(valid_address) != -1, \
                    "YES button on deletion confirmation does not yield deletion statement"
                assert second_response_2.text == "Click an address from the list below or add a node:", \
                    "YES button on deletion confirmation does not go back to thornodes menu"
                assert second_response_2.reply_markup.inline_keyboard[0][0].text == "1️⃣ ADD NODE", "Node is NOT deleted after deletion"
            else:
                self.click_button("NO ❌")
                time.sleep(3)
                second_response = next(self.telegram.iter_history(self.BOT_ID))
                assert second_response.text.find("Address: " + valid_address) != -1, \
                    "NO button on single address deletion confirmation does not go back to Thornode details"
            print("➖ REMOVE Address with confirmation=" + str(confirm) + " ✅")
            print("------------------------")

    def assert_delete_all_addresses(self, confirm):
        with self.telegram:
            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)
            self.click_button("➕ ADD ALL")

            self.telegram.send_message(self.BOT_ID, "/start")
            time.sleep(3)
            self.telegram.send_message(self.BOT_ID, "📡 MY NODES")
            time.sleep(3)
            self.click_button("➖ REMOVE ALL")

            first_response = next(self.telegram.iter_history(self.BOT_ID))

            assert first_response.text == '⚠️ Do you really want to remove all THORNodes from your monitoring list? ⚠️', \
                "➖ REMOVE ALL button does not work!"

            if confirm:
                self.click_button("YES ✅")
                second_response_1 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 1, None))
                second_response_2 = next(itertools.islice(self.telegram.iter_history(self.BOT_ID), 0, None))
                assert second_response_1.text == "❌ Deleted all THORNodes! ❌", \
                    "YES button on ➖ REMOVE ALL confirmation does not yield deletion statement"
                assert second_response_2.text == "Click an address from the list below or add a node:", \
                    "YES button on ➖ REMOVE ALL confirmation does not go back to 📡 MY NODES menu"
                assert second_response_2.reply_markup.inline_keyboard[0][0].text == '1️⃣ ADD NODE' and \
                    "Nodes are not deleted after YES button on ➖ REMOVE ALL confirmation"
            else:
                self.click_button("NO ❌")
                time.sleep(3)
                second_response = next(self.telegram.iter_history(self.BOT_ID))
                assert second_response.text == "Click an address from the list below or add a node:", \
                    "NO button on ➖ REMOVE ALL confirmation does not go back to 📡 MY NODES menu"

            print("➖ REMOVE ALL with confirmation=" + str(confirm) + " ✅")
            print("------------------------")

    def assert_catch_up_notification(self, catching_up):
        with self.telegram:
            with open('mock_files/status.json') as json_read_file:
                node_data = json.load(json_read_file)

            node_data['result']['sync_info']['catching_up'] = catching_up

            with open('mock_files/status.json', 'w') as json_write_file:
                json.dump(node_data, json_write_file)
            time.sleep(7)

            response = next(self.telegram.iter_history(self.BOT_ID))

            if catching_up:
                expected_response = 'The Node is behind the latest block height and catching up!'
            else:
                expected_response = 'The node caught up to the latest block height again!'

            assert response.text.find(expected_response) != -1, "Expected '" + expected_response + \
                                                                      "'\nbut got\n'" + response.text + "'"

            print("Check catch up status with catching_up=" + str(catching_up) + " ✅")
            print("------------------------")


if __name__ == '__main__':
    unittest.main()
