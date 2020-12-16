from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from constants.globals import SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT
from handlers.chat_helpers import try_message
from service.utils import get_slash_points_threshold


def show_settings(update, context):
    current_threshold = get_slash_points_threshold(context)
    keyboard = [[InlineKeyboardButton(f'🔪 ({current_threshold} points) Slash points notification threshold',
                                      callback_data='set_threshold')]]
    was_back_button_clicked = hasattr(update.callback_query, 'data') and (
            update.callback_query.data.split("-")[-1] == "edit")
    title = 'Manage your *THORNode Bot* 🤖'

    if was_back_button_clicked:
        update.callback_query.edit_message_text(text=title,
                                                parse_mode='markdown',
                                                reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        try_message(context=context,
                    chat_id=update.effective_message.chat_id,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    text=title)


def set_threshold_menu(update, context):
    query = update.callback_query
    current_threshold = get_slash_points_threshold(context)

    keyboard = [[InlineKeyboardButton(f'⬅️ BACK', callback_data='show_settings-edit')]]

    text = f"If the slash points of a monitored node change, you'll get notified only when the change is greater " \
           f"than the *slash points notification threshold*." \
           f" For example, when you set it to 1 you will get the notification " \
           f"when the change of points is 2 or more.\n\n" \
           f"Slash points notification threshold: *{current_threshold}*\n" \
           f"Default: *{SLASH_POINTS_NOTIFICATION_THRESHOLD_DEFAULT}* \n" \
           f"(0 = always notify)\n\n" \
           f"*Insert threshold for slash points notification*"
    context.chat_data['expected'] = 'change_threshold'

    query.edit_message_text(
        text=text,
        parse_mode='markdown',
        reply_markup=InlineKeyboardMarkup(keyboard))


def handle_change_threshold(update, context):
    new_number_str = update.message.text

    try:
        new_threshold = int(new_number_str)

        if new_threshold < 0:
            raise
    except:
        update.message.reply_text(
            '⛔️ This is not a correct input! Must be an integer *>= 0* ⛔️\n\n'
            'Try again.',
            parse_mode='markdown')
        context.chat_data['expected'] = 'change_threshold'
        return

    set_slash_points_threshold(new_threshold, context)

    text = f'✅ Successfully set your new threshold for slash points notification as *{new_threshold}*'
    if new_threshold == 0:
        text += f'\nYou will be always notified!'

    update.message.reply_text(text, parse_mode='markdown')
    show_settings(update, context)


def set_slash_points_threshold(new_val, context):
    if int(new_val) < 0:
        raise Exception("Threshold must be a positive integer")

    settings = context.bot_data.setdefault("settings", {})
    settings["slash_points_threshold"] = new_val
