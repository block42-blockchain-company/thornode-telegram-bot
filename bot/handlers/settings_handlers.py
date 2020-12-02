from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.chat_helpers import try_message


def show_settings(update, context):
    current_threshold = 0

    keyboard = [[InlineKeyboardButton(f'🔪 ({current_threshold} pts) Slash points notifications threshold',
                                      callback_data='set_threshold')]]

    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text="Manage your *THORNode Bot* 🤖",
                reply_markup=InlineKeyboardMarkup(keyboard))


def set_threshold(update, context):
    keyboard = [[InlineKeyboardButton('SET DEFAULT', callback_data='set_threshold')]]
    current_threshold = 0

    text = f"Slash points notifications threshold: *{current_threshold}*\n\n"
    text = f"Insert threshold for slash points notifications"


    try_message(context=context,
                chat_id=update.effective_message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard))
