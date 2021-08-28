import logging
import re
from utils import DialogueStates
from db import DBConnection
from user_message import UserMessage
from callbacks import Callbacks

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, \
    ParseMode, CallbackQuery, BotCommand, ContentType


class DormBot:
    f = open("bot_token.txt", "r")
    bot_token = f.read().strip()
    f.close()

    # Initialize bot and dispatcher
    bot = Bot(token=bot_token)
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(LoggingMiddleware())

    db_connection = DBConnection()

    default_answers = db_connection.get_answers()

    def __init__(self):

        executor.start_polling(self.dp, on_shutdown=DormBot.shutdown, skip_updates=True)

    @staticmethod
    async def set_commands():
        commands = [
            BotCommand(command="/start", description="Старт"),
            BotCommand(command="/help", description="Информационная справка по работе с ботом")
        ]
        await DormBot.bot.set_my_commands(commands)

    @staticmethod
    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: Message):
        """
        This handler will be called when user sends `/start` or `/help` command
        """
        state = DormBot.dp.current_state(user=message.from_user.id)
        if DormBot.db_connection.select_users(user_id=message.from_user.id):
            button_questions = KeyboardButton('Хочу спросить.')
            button_request = KeyboardButton('Хочу оставить заявку.')
            button_idea = KeyboardButton('Есть идея/пожелание/предложение.')
            greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            greet_kb.add(button_questions)
            greet_kb.add(button_request)
            greet_kb.add(button_idea)

            if DormBot.db_connection.select_users(user_id=message.from_user.id)[0][3] == 'admin':
                button_add_answer = KeyboardButton('Добавить стандартный вопрос.')
                button_del_answer = KeyboardButton('Удалить стандартный вопрос.')
                greet_kb.add(button_add_answer)
                greet_kb.add(button_del_answer)

            await message.answer(f"Привет! {message.from_user.first_name}!",
                                 parse_mode=ParseMode.HTML, reply_markup=greet_kb
                                 )
        else:
            await DialogueStates.registration.set()
            await message.answer(f"Вам необходимо пройти регистраци."
                                 f"Введите свои данные в соответствии со следующей формой: "
                                 f"name surname group room."
                                 )

    # @staticmethod
    # @dp.message_handler(content_types=['photo'])
    # async def handle_docs_photo(message):
    #     print('get_photo')

    @staticmethod
    @dp.message_handler(state='*', content_types=['photo', 'text'])
    async def message_handler(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)
        state_name = await state.get_state()
        print(message.content_type == ContentType.PHOTO)
        if (not DormBot.db_connection.select_users(user_id=message.from_user.id)) and \
                (not (state_name == 'DialogueStates:registration')):
            await DialogueStates.registration.set()
            return await message.answer(f"Вам необходимо пройти регистраци."
                                        f"Введите свои данные в соответствии со следующей формой: "
                                        f"name surname group room."
                                        )

        msg = UserMessage(message, state, DormBot.bot, DormBot.db_connection, DormBot.default_answers)
        await msg.message_parse()
        if msg.output:
            await message.reply(msg.output, reply=False)
        if msg.media:
            await DormBot.bot.send_photo(msg.user_id, msg.media)
        return 0

    @staticmethod
    @dp.callback_query_handler()
    async def inline_callback(callback_query: CallbackQuery):
        state = DormBot.dp.current_state(user=callback_query.from_user.id)
        callback = Callbacks(callback_query, state)
        await callback.process()
        await DormBot.bot.answer_callback_query(callback_query.id)
        await DormBot.bot.send_message(callback_query.from_user.id, callback.output)

    @staticmethod
    async def shutdown(dispatcher: Dispatcher):
        await dispatcher.storage.close()
        await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    bot = DormBot()
    DormBot.set_commands()
