import re

from telegram.error import BadRequest

from handlers.network_info_handlers import *
from handlers.other_nodes_handlers import *
from handlers.settings_handlers import show_settings, set_threshold_menu, handle_change_threshold
from handlers.thornodes_handlers import *
from jobs.jobs import start_user_job


@run_async
def on_start_command(update, context):
    """
    Send start message and display action buttons.
    """

    if not is_admin(update, context):
        return

    # Start job for user
    if 'job_started' not in context.user_data:
        start_user_job(context, update.message.chat.id)

    text = 'Heil ok sæll! I am your THORNode Bot runaning on ' + NETWORK_TYPE + '. 🤖\n\n'
    text += 'I will notify you about changes of your THORNode\'s\n' \
            '- *Status*\n' \
            '- *Bond*\n' \
            '- *Slash Points*\n' \
            '- if your *Block Height* gets stuck\n' \
            '- if your *Midgard API* gets unhealthy\n\n' \
            'You will get a notification\n' \
            '- once any node *upgrades its version*\n' \
            '- after *successful churning*\n' \
            '- if thorchain becomes *insolvent*\n\n'
    text += 'If you specified Node IPs, I notify you about changes of your *Binance, ' \
            'Ethereum and Bitcoin Node\'s health*.\n\n'
    text += 'Moreover, in the Network section you can display\n' \
            '- the *status of the whole network*\n' \
            '- the correct *vault addresses*.\n' \
            '- the current *solvency* status.\n'

    # Send message
    try_message_with_home_menu(context=context,
                               chat_id=update.message.chat.id,
                               text=text)


@run_async
def dispatch_query(update, context):
    """
    Call right function depending on the button clicked
    """

    query = update.callback_query
    query.answer()
    data = query.data

    if not is_admin(update, context):
        return

    context.user_data['expected'] = None
    edit = True
    call = None

    if data == 'show_all_thorchain_nodes':
        call = show_all_thorchain_nodes
    elif data == 'show_network_stats':
        call = show_network_stats
    elif data.startswith('show_settings'):
        call = show_settings
    elif data == 'solvency':
        call = solvency_stats
    elif data == 'vault_key_addresses':
        call = show_vault_key_addresses
    elif data == 'add_thornode':
        call = add_thornode
    elif data == 'confirm_add_all_thornodes':
        call = confirm_add_all_thornodes
    elif data == 'add_all_thornodes':
        call = add_all_thornodes
    elif data == 'confirm_delete_all_thornodes':
        call = confirm_delete_all_thornodes
    elif data == 'delete_all_thornodes':
        call = delete_all_thornodes
    elif re.match('thornode_details', data):
        call = thornode_details
    elif data == 'confirm_thornode_deletion':
        call = confirm_thornode_deletion
    elif data == 'delete_thornode':
        call = delete_thornode
    elif data == 'change_alias':
        call = change_alias
    elif data == 'show_nodes_thor':
        call = show_my_thorchain_nodes_menu
    elif data == 'show_nodes_other':
        call = show_other_nodes_menu
    elif data.startswith("other_node_details"):
        call = show_other_nodes_details
    elif data == 'set_threshold':
        call = set_threshold_menu
    else:
        edit = False

    # Catch any 'Message is not modified' error by removing the keyboard
    if edit:
        try:
            context.bot.edit_message_reply_markup(
                reply_markup=None,
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id)
        except BadRequest as e:
            if 'Message is not modified' in e.message:
                pass
            else:
                raise

    if call:
        # noinspection PyDeprecation
        call = asyncio.coroutine(call)
        return asyncio.run(call(update, context))


@run_async
def dispatch_plain_input_query(update, context):
    """
    Handle if the users sends a message
    """

    if not is_admin(update, context):
        return

    message = update.message.text
    expected = context.user_data.pop('expected', None)

    if message == '📡 MY NODES':
        return on_my_nodes_clicked(update, context)
    elif message == '🌎 NETWORK':
        return show_network_menu(update, context)
    elif message == '👀 SHOW ALL':
        return show_all_thorchain_nodes(update, context)
    elif message == '⚙️ SETTINGS':
        return show_settings(update, context)
    elif expected == 'add_node':
        return handle_add_node(update, context)
    elif expected == 'change_alias':
        return handle_change_alias(update, context)
    elif expected == 'change_threshold':
        return handle_change_threshold(update, context)


@run_async
def on_my_nodes_clicked(update, context):
    keyboard = [[
        InlineKeyboardButton('📡 THORCHAIN NODES', callback_data='show_nodes_thor')], [
        InlineKeyboardButton('📡 OTHER CHAIN NODES', callback_data='show_nodes_other'),
    ]]

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text="*What type of nodes do you want to see?*\n"
                     "Note that Bitcoin and Ethereum nodes need to be added manually.",
                reply_markup=InlineKeyboardMarkup(keyboard))


def error_handler(update, context):
    """
    Log error.
    """

    logger.warning('Update "%s" caused error: %s', update, context.error)
