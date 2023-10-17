import asyncio
import logging
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton

from core import UserInputCheck, Requester, my_formatter


load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
info_logger = logging.getLogger()
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('bot.log', 'a', 'utf-8')
info_handler.setFormatter(my_formatter)
info_logger.addHandler(info_handler)

TOKEN = os.getenv("TOKEN")
dp = Dispatcher()

btn1 = KeyboardButton(text="EUR RUR")
btn2 = KeyboardButton(text="USD RUR")
btn3 = KeyboardButton(text="TRY RUR")
btn4 = KeyboardButton(text="USD TRY")
btn5 = KeyboardButton(text="EUR TRY")
markup = ReplyKeyboardMarkup(keyboard=[[btn1], [btn2], [btn3], [btn4], [btn5]],
                             resize_keyboard=False)

start_time = time.time()
current_table, wrong_input = Requester.get_request()
info_logger.info(f'Бот выполнил запрос. Ошибка: {wrong_input}')


@dp.message(Command('start', 'help'))
async def command_handler(message: Message) -> None:
    info_logger.info(f'Боту пришло сообщение: "{message.text}'
                     f' от {message.from_user.first_name}"')
    answer = f'Приветствую, {message.from_user.first_name}! ' \
             f'Я помогу тебе перевести валюту по курсу ЦБ. ' \
             f'Введи код валюты, из которой хочешь конвертировать,' \
             f' и код валюты, в которую хочешь конвертировать, через пробел. ' \
             f'Например: EUR USD.При необходимости добавь количество ' \
             f'конвертируемой валюты. Например:  RUR EUR 100. \n' \
             f'Для того, чтобы посмотреть доступные валюты введи /values'
    await message.reply(answer, reply_markup=markup)
    info_logger.info(f'Бот ответил: "{answer}"')


@dp.message(Command('values'))
async def values_handler(message: Message) -> None:
    global current_table, wrong_input, start_time
    info_logger.info(f'Боту пришло сообщение: "{message.text}'
                     f' от {message.from_user.first_name}"')
    if int(time.time()-start_time) > 1800 or wrong_input:
        current_table, wrong_input = Requester.get_request()
        info_logger.info(f'Бот выполнил запрос. Ошибка: {wrong_input}')
        start_time = time.time()
    if wrong_input is None:
        current_list = Requester.currency_list_maker(current_table)
        answer = current_list
        await message.reply(answer, reply_markup=markup)
        info_logger.info(f'Бот ответил: "{answer}"')
    else:
        await message.reply(wrong_input, reply_markup=markup)
        info_logger.info(f'Бот ответил: "{wrong_input}"')


@dp.message()
async def message_handler(message: types.Message) -> None:
    global current_table, wrong_input, start_time
    info_logger.info(f'Боту пришло сообщение: "{message.text}'
                     f' от {message.from_user.first_name}"')
    currency_1, currency_2, quantity, wrong_input = \
        UserInputCheck.first_check(message.text)
    if wrong_input is None:
        if int(time.time() - start_time) > 1800:
            current_table, wrong_input = Requester.get_request()
            info_logger.info(f'Бот выполнил запрос. Ошибка: {wrong_input}')
            start_time = time.time()
        if wrong_input is None:
            currency1_rate, wrong_input, nominal1 = UserInputCheck.second_check(
                currency_1, current_table)
            if wrong_input is None:
                currency2_rate, wrong_input, nominal2 = \
                    UserInputCheck.second_check(currency_2, current_table)
                if wrong_input is None:
                    answer = str(quantity) + ' ' + currency_1.upper() + ' = ' +\
                             str(round(
                                 ((currency1_rate * nominal2)/
                                  (currency2_rate * nominal1)) * quantity,
                                 2)) \
                             + ' ' + currency_2.upper() + ' по курсу ЦБ'
                    await message.reply(answer, reply_markup=markup)
                    info_logger.info(f'Бот ответил: "{answer}"')
    if wrong_input:
        await message.reply(wrong_input, reply_markup=markup)
        info_logger.info(f'Бот ответил: "{wrong_input}"')


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
