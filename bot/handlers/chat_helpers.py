from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, TelegramError
from constants.globals import *


def try_message_with_home_menu(context, chat_id, text):
    keyboard = get_home_menu_buttons()
    try_message(context=context,
                chat_id=chat_id,
                text=text,
                reply_markup=ReplyKeyboardMarkup(keyboard,
                                                 resize_keyboard=True)
                )


def try_message_to_all_users(context, text):
    for chat_id in context.dispatcher.chat_data.keys():
        try_message_with_home_menu(context, chat_id=chat_id, text=text)


def get_home_menu_buttons():
    """
    Return keyboard buttons for the home menu
    """

    keyboard = [[KeyboardButton('📡 MY NODES')],
                [KeyboardButton('👀 SHOW ALL'), KeyboardButton('🌎 NETWORK')]]

    return keyboard


def show_text_input_message(update, text):
    """
    Initiate a conversation and prompt for user input.
    """

    # Enable message editing
    query = update.callback_query

    # Send message
    query.edit_message_text(text)


def try_message(context, chat_id, text, reply_markup=None):
    """
    Send a message to a user.
    """

    if context.job and not context.job.enabled:
        return

    try:
        context.bot.send_message(chat_id,
                                 text,
                                 parse_mode='markdown',
                                 reply_markup=reply_markup,
                                 isgroup=is_group_chat(chat_id))
    except TelegramError as e:
        if 'bot was blocked by the user' in e.message:
            print("Telegram user " + str(chat_id) +
                  " blocked me; removing him from the user list")
            del context.dispatcher.chat_data[chat_id]
            del context.dispatcher.chat_data[chat_id]
            del context.dispatcher.persistence.chat_data[chat_id]
            del context.dispatcher.persistence.chat_data[chat_id]

            # Somehow session.data does not get updated if all users block the bot.
            # That makes problems on bot restart. That's why we delete the file ourselves.
            if len(context.dispatcher.persistence.chat_data) == 0:
                if os.path.exists(session_data_path):
                    os.remove(session_data_path)
            context.job.enabled = False
            context.job.schedule_removal()
        else:
            print("Got Error\n" + str(e) + "\nwith telegram user " +
                  str(chat_id))


# TODO remove/fix me
def show_confirmation_menu(update, text, keyboard):
    """
    "Are you sure?" - "YES" | "NO"
    """

    query = update.callback_query

    query.edit_message_text(text,
                            parse_mode='markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard))


def build_2_columns_keyboard(buttons):
    count = 0
    keyboard = [[]]

    for button in buttons:
        if count % 2 == 0:
            keyboard.append([button])
        else:
            keyboard[-1].append(button)

        count += 1

    return keyboard


def is_admin(update, context):
    if ALLOWED_USER_IDS == 'ALL':
        return True
    elif update.effective_chat.id not in ALLOWED_USER_IDS:
        try_message(context, update.effective_chat.id, f"❌ You are not an Admin! ❌\n"
                                                       f"I'm *THORNode Bot*, I'm a loyal bot.")
        return False
    return True


def is_group_chat(chat_id: int):
    return chat_id < 0
