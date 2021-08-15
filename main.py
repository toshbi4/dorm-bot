import logging
import re

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, \
    Message, ParseMode


class DormBot:
    f = open("bot_token.txt", "r")
    bot_token = f.read().strip()
    f.close()

    # Initialize bot and dispatcher
    bot = Bot(token=bot_token)
    dp = Dispatcher(bot)
    state = 0

    def __init__(self):

        executor.start_polling(self.dp, skip_updates=True)

    @staticmethod
    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: Message):
        """
        This handler will be called when user sends `/start` or `/help` command
        """

        button_questions = KeyboardButton('Хочу спросить.')
        greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        greet_kb.add(button_questions)

        await message.answer(f"Привет! {message.from_user.first_name}! 👋",
                             parse_mode=ParseMode.HTML, reply_markup=greet_kb
                             )

    @staticmethod
    @dp.message_handler(text=['Хочу спросить.'])
    async def answer(message: Message):

        # msg = message.text.lower()
        # if not msg.find('душ') == -1:
        #     await message.answer(f"Вот тебе расписание душа.")
        # elif not msg.find('зал') == -1:
        #     await message.answer(f"Вот тебе расписание зала.")
        # elif not msg.find('прачечной') == -1:
        #     await message.answer(f"Вот тебе расписание прачечной.")
        # else:
        DormBot.state = 1
        await message.answer(f"Задавай свой вопрос.")

    @staticmethod
    @dp.message_handler()
    async def default_question(message: Message):
        print(DormBot.state)
        if DormBot.state == 1:
            await message.answer(f"Ты задаешь вопрос.")
        else:
            await message.answer(f"Ты написал какую-то дичь, черт.")


if __name__ == '__main__':
    bot = DormBot()
