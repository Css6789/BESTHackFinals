import os

import telebot
from telebot import types
from telebot.util import quick_markup
from constants import *
from collections import defaultdict
from form import Form, FormToVerifyString, CategoryEnum
from utils import str_eq
from dotenv import load_dotenv
from bot_channel import *

class IssueDiscussions:
    def __init__(self):
        self.request_unix_time = 0
        self.response_delay = 0

load_dotenv()
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

user_dict = defaultdict(Form)
channel_post_dict = defaultdict(IssueDiscussions)
hash_to_channel_message_id = {}


@bot.message_handler(commands=['help', 'start'])
def start(message):
    bot.send_message(message.from_user.id,
                     "Привет, я твой бот-ассистент для навигации и связи с инженерами Авито (чтобы продолжить, "
                     "введите /request_category)")


@bot.message_handler(commands=['request_category'])
def request_category(message):
    markup = quick_markup({
        'Статус заказа завис': {'callback_data': TRACK_ORDER_CALLBACK},
        'Деньги не вернулись / зависли': {'callback_data': GET_REFUND_CALLBACK},
        'Изменить параметры заказа': {'callback_data': CHANGE_ORDER_CALLBACK},
        'Проблемы с уведомлениями': {'callback_data': NOTIFICATION_PROBLEM_CALLBACK},
        'Другое': {'callback_data': OTHER_CALLBACK},
    }, row_width=1)
    bot.send_message(message.from_user.id, "Выберите категорию запроса (После этого введите команду /text)",
                     reply_markup=markup)


#############################
##### Handle Categories #####
#############################

@bot.callback_query_handler(func=lambda message: str_eq(message.data, TRACK_ORDER_CALLBACK))
def order_stuck(message):
    user_dict[message.message.chat.id].selected_category = CategoryEnum.TRACK_ORDER

    msg = bot.send_message(message.from_user.id, Category.TRACK_ORDER[1][0][0])
    bot.register_next_step_handler(msg, Category.TRACK_ORDER[1][0][1], Category.TRACK_ORDER[1][1:])


@bot.callback_query_handler(func=lambda message: str_eq(message.data, GET_REFUND_CALLBACK))
def money_stuck(message):
    user_dict[message.message.chat.id].selected_category = CategoryEnum.GET_REFUND

    msg = bot.send_message(message.from_user.id, Category.GET_REFUND[1][0][0])
    bot.register_next_step_handler(msg, Category.GET_REFUND[1][0][1], Category.GET_REFUND[1][1:])


@bot.callback_query_handler(func=lambda message: str_eq(message.data, CHANGE_ORDER_CALLBACK))
def delivery_delay(message):
    user_dict[message.message.chat.id].selected_category = CategoryEnum.CHANGE_ORDER

    msg = bot.send_message(message.from_user.id, Category.CHANGE_ORDER[1][0][0])
    bot.register_next_step_handler(msg, Category.CHANGE_ORDER[1][0][1], Category.CHANGE_ORDER[1][1:])

@bot.callback_query_handler(func=lambda message: str_eq(message.data, NOTIFICATION_PROBLEM_CALLBACK))
def delivery_delay(message):
    user_dict[message.message.chat.id].selected_category = CategoryEnum.NOTIFICATION_PROBLEM

    msg = bot.send_message(message.from_user.id, Category.NOTIFICATION_PROBLEM[1][0][0])
    bot.register_next_step_handler(msg, Category.NOTIFICATION_PROBLEM[1][0][1], Category.NOTIFICATION_PROBLEM[1][1:])

@bot.callback_query_handler(func=lambda message: str_eq(message.data, OTHER_CALLBACK))
def other_category(message):
    user_dict[message.message.chat.id].selected_category = CategoryEnum.OTHER

    msg = bot.send_message(message.from_user.id, Category.OTHER[1][0][0])
    bot.register_next_step_handler(msg, Category.OTHER[1][0][1], Category.OTHER[1][1:])


#############################
######### Bot Logic #########
#############################
def ask_for_uid(message, *args):
    user_dict[message.chat.id].user_id = message.text

    continue_the_process(message, args)


def ask_for_order_id(message, *args):
    user_dict[message.chat.id].order_id = message.text

    continue_the_process(message, args)


def ask_for_current_order_status(message, *args):
    user_dict[message.chat.id].current_order_status = message.text

    continue_the_process(message, args)


def continue_the_process(message, args):
    print(message.text, args)
    if len(args[0]) > 0:
        msg = bot.send_message(message.from_user.id, args[0][0][0])
        bot.register_next_step_handler(msg, args[0][0][1], args[0][1:])
    else:
        # All data is collected
        print("Finished!")
        user_dict[message.chat.id].additional_data = message.text

        final_form = user_dict[message.chat.id]
        verify_str = FormToVerifyString(final_form)

        markup = quick_markup({
            'Всё верно (YES)': {'callback_data': FORM_CORRECT_CALLBACK},
            'Начать заново (NO)': {'callback_data': FORM_INCORRECT_CALLBACK},
        }, row_width=1)
        print(verify_str)
        bot.send_message(message.from_user.id,
                         "Проверьте введённые вами данные. Выберите вариант (YES) на клавиатуре, "
                         "если всё правильно, или (NO), сели что-то требует изменения\n\n"
                         + verify_str, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda message: str_eq(message.data, FORM_CORRECT_CALLBACK))
def form_correct_confirmed(callback):
    form = user_dict[callback.message.chat.id]
    msg = send_form_to_channel(bot, form)
    hash_to_channel_message_id[hash(msg.text)] = msg.message_id

@bot.callback_query_handler(func=lambda message: str_eq(message.data, FORM_INCORRECT_CALLBACK))
def form_incorrect_confirmed(callback):
    user_dict[callback.message.chat.id] = Form()
    bot.send_message(callback.from_user.id, "Форма очищена. Введите /start, чтобы начать сначала.")

@bot.message_handler(commands=['takeon'])
def take_on(message):
    original_request = message.reply_to_message
    request_unix_time = original_request.date
    response_delay = message.date - request_unix_time

    channel_post_dict[original_request.message_id].request_unix_time = request_unix_time
    channel_post_dict[original_request.message_id].response_delay = response_delay
    bot.reply_to(message, "Thanks for taking on this issue. Response delay: " + str(response_delay))

@bot.message_handler(commands=['finish'])
def finish_request(message):
    original_request = message.reply_to_message
    finish_unix_time = message.date
    request_solve_time = finish_unix_time - channel_post_dict[original_request.message_id].request_unix_time

    bot.reply_to(message, "This issue is closed in " + str(request_solve_time) + " seconds.")
    feed_channel_post_id = hash_to_channel_message_id[hash(original_request.text)]
    bot.delete_message(FEED_CHANNEL_ID, feed_channel_post_id)

class Category:
    NOT_SELECTED = [0, []]
    TRACK_ORDER = [1, [("Пожалуйста, введите id пользователя с проблемой", ask_for_uid),
                       ("Пожалуйста, введите номер заказа", ask_for_order_id),
                       ("Пожалуйста, введите текущий статус заказа", ask_for_current_order_status), (
                           "Введите какую-либо дополнительную информацию, если таковая имеется",
                           lambda msg, *args: continue_the_process(msg, args))]] # Завис статус заказа
    GET_REFUND = [2, [("Пожалуйста, введите id пользователя с проблемой", ask_for_uid),
                       ("Пожалуйста, введите номер заказа", ask_for_order_id),
                       ("Пожалуйста, введите текущий статус заказа", ask_for_current_order_status), (
                           "Введите какую-либо дополнительную информацию, если таковая имеется",
                           lambda msg, *args: continue_the_process(msg, args))]] # Зависли деньги
    CHANGE_ORDER = [3, [("Пожалуйста, введите id пользователя с проблемой", ask_for_uid),
                       ("Пожалуйста, введите номер заказа", ask_for_order_id),
                       ("Пожалуйста, введите текущий статус заказа", ask_for_current_order_status), (
                           "Введите какую-либо дополнительную информацию, если таковая имеется",
                           lambda msg, *args: continue_the_process(msg, args))]] # Изменить параметры заказа
    NOTIFICATION_PROBLEM = [4, [("Пожалуйста, введите id пользователя с проблемой", ask_for_uid), (
                            "Введите какую-либо дополнительную информацию, если таковая имеется",
                            lambda msg, *args: continue_the_process(msg, args))]] # Проблемы с уведомлениями
    OTHER = [5, [(
                            "Введите какую-либо дополнительную информацию, если таковая имеется",
                            lambda msg, *args: continue_the_process(msg, args))]] # Другие проблемы


bot.polling()
