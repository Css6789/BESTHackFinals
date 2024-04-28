from enum import Enum


class Form:
    def __init__(self):
        self.selected_category = CategoryEnum.NOT_SELECTED
        self.user_id = None
        self.order_id = None
        self.current_order_status = None
        self.additional_data = None


def FormToVerifyString(form):
    print(form.selected_category)
    s = ''
    if form.selected_category != CategoryEnum.NOT_SELECTED: s += '*Выбранная категория:* ' + form.selected_category.value + '\n'
    if form.user_id != None: s += '*ID Пользователя:* ' + form.user_id + '\n'
    if form.order_id != None: s += '*Номер Заказа:* ' + form.order_id + '\n'
    if form.current_order_status != None: s += '*Текущий статус заказа:* ' + form.current_order_status + '\n'
    if form.additional_data != None: s += '*Дополнительная информация:* ' + form.additional_data + '\n'
    return s


def FormToRequestString(form):
    s = '*памагите техподу (НОВЫЙ ЗАПРОС)*\n\n'
    if form.selected_category != CategoryEnum.NOT_SELECTED: s += '*Категория запроса:* ' + form.selected_category.value + '\n'
    if form.user_id is not None: s += '*ID Пользователя:* ' + form.user_id + '\n'
    if form.order_id is not None: s += '*Номер Заказа:* ' + form.order_id + '\n'
    if form.current_order_status is not None: s += '*Текущий статус заказа:* ' + form.current_order_status + '\n'
    if form.additional_data is not None: s += '*Дополнительная информация:* ' + form.additional_data + '\n'
    return s


class CategoryEnum(str, Enum):
    NOT_SELECTED = "Не выбрано"
    TRACK_ORDER = "Статус заказа завис" # #status_stuck
    GET_REFUND = "Деньги не вернулись" # #money_refund
    CHANGE_ORDER = "Задержка доставки" # #delivery_delay
    NOTIFICATION_PROBLEM = "Проблема с уведомлениями" # #notification_issue
    OTHER_CATEGORY = "Другое" # #other_problems
