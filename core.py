import requests
import json
import logging


class CurrencyException(Exception):

    def __str__(self):
        return 'Неизвестная валюта'


class MessageFormatException(Exception):

    def __str__(self):
        return 'Неверный формат ввода запроса'


class CurrencyDuplicationException(Exception):

    def __str__(self):
        return 'Запрос остановлен. Выбраны одинаковые валюты для перевода'


class ConnectionException(Exception):

    def __str__(self):
        return 'Сервер недоступен.'


my_formatter = logging.Formatter(
    '%(filename)s %(asctime)s %(levelname)s %(message)s')

error_handler = logging.FileHandler('bot_errors.log', 'a', 'utf-8')
error_handler.setFormatter(my_formatter)
error_logger = logging.getLogger('Error')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)


class UserInputCheck:

    @staticmethod
    def first_check(message):
        checking_message = message.split()
        currency_1, currency_2, quantity, wrong_input = None, None, None, None
        if len(checking_message) == 2:
            quantity = 1
            try:
                for mes in checking_message:
                    if len(mes) != 3:
                        raise CurrencyException()
                    elif not mes.isalpha():
                        raise CurrencyException()
                    else:
                        currency_1, currency_2 = checking_message[0].upper(), \
                            checking_message[1].upper()
            except CurrencyException as err:
                wrong_input = f'{err} {mes}'
                error_logger.error(wrong_input)
        elif len(checking_message) == 3:
            try:
                for mes in checking_message[:2]:
                    if len(mes) != 3:
                        raise CurrencyException()
                    elif not mes.isalpha():
                        raise CurrencyException()
                    else:
                        currency_1, currency_2 = checking_message[0].upper(), \
                            checking_message[1].upper()
            except CurrencyException as err:
                wrong_input = f'{err} {mes}'
                error_logger.error(wrong_input)
            try:
                quantity = float(checking_message[2].replace(',', '.'))
                if quantity <= 0:
                    raise ValueError()
            except ValueError:
                wrong_input = f'Неверно введено количество переводимой' \
                              f' валюты {checking_message[2]}'
                error_logger.error(wrong_input)
        else:
            try:
                raise MessageFormatException()
            except MessageFormatException as err:
                wrong_input = f'{err} {message}. Формат сообщения должен быть:'\
                              f' USD EUR 100'
                error_logger.error(wrong_input)
        try:
            if (not wrong_input) and currency_1 == currency_2:
                raise CurrencyDuplicationException()
        except CurrencyDuplicationException as err:
            wrong_input = f'{err} {currency_1}'
            error_logger.error(wrong_input)
        return currency_1, currency_2, quantity, wrong_input

    @staticmethod
    def second_check(current, current_table):
        current_rate, wrong_input = None, None
        try:
            if current in current_table.keys():
                current_rate = current_table[current]['Value']
                nominal = current_table[current]['Nominal']
            else:
                raise CurrencyException()
        except CurrencyException as err:
            wrong_input = f'{err} {current}'
            error_logger.error(wrong_input)
        return current_rate, wrong_input, nominal


class Requester:

    @staticmethod
    def get_request():
        current_table, wrong_input = None, None
        request = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        if request.status_code == 200:
            current_table = json.loads(request.content)['Valute']
            addition_dict = {'RUR': {
                'ID': '????',
                'NumCode': '643',
                'CharCode': 'RUR',
                'Nominal': 1,
                'Name': 'Российский рубль',
                'Value': 1,
                'Previous': 1}}
            current_table.update(addition_dict)
        else:
            try:
                raise ConnectionException()
            except ConnectionException as err:
                wrong_input = f'{err} Код ошибки: {request.status_code}'
                error_logger.error(wrong_input)
        return current_table, wrong_input

    @staticmethod
    def currency_list_maker(current_table):
        currency_list = ''
        for current in current_table.keys():
            currency_list += f'{current} - {current_table[current]["Name"]}\n'
        currency_list = currency_list[:-1]
        return currency_list
