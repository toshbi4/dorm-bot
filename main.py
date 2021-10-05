import asyncio
from utils import DialogueStates
from db import DBConnection
from user_message import UserMessage
from callbacks import Callbacks

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, \
    ParseMode, CallbackQuery, BotCommand, ContentType
from aiogram.utils.exceptions import Throttled


class DormBot:
    f = open("cfg/bot_token.txt", "r")
    bot_token = f.read().strip()
    f.close()

    message_delay = 5

    # Initialize bot and dispatcher
    bot = Bot(token=bot_token)
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(LoggingMiddleware())

    db_connection = DBConnection()

    default_answers = db_connection.get_answers()
    admin_password = 0

    def __init__(self):

        loop = asyncio.get_event_loop()
        loop.call_later(DormBot.message_delay, DormBot.repeat, DormBot.send_to_administration, loop)
        executor.start_polling(self.dp, on_shutdown=DormBot.shutdown, skip_updates=True, loop=loop)

    @staticmethod
    async def set_commands():
        commands = [
            BotCommand(command="/start", description="Старт"),
            BotCommand(command="/help", description="Информационная справка по работе с ботом")
        ]
        await DormBot.bot.set_my_commands(commands)

    @staticmethod
    @dp.message_handler(commands=['start'])
    async def send_welcome(message: Message):
        """
        This handler will be called when user sends `/start` command
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

            if DormBot.db_connection.select_users(user_id=message.from_user.id)[0][3] in ['admin', 'super_admin']:
                button_add_answer = KeyboardButton('Добавить стандартный вопрос.')
                button_del_answer = KeyboardButton('Удалить стандартный вопрос.')
                button_get_users = KeyboardButton('Получить список пользователей.')
                button_del_user = KeyboardButton('Удалить пользователя.')
                button_ban_user = KeyboardButton('Забанить пользователя.')
                button_unban_user = KeyboardButton('Разбанить пользователя.')
                greet_kb.add(button_add_answer)
                greet_kb.add(button_del_answer)
                greet_kb.add(button_get_users)
                greet_kb.add(button_del_user)
                greet_kb.add(button_ban_user)
                greet_kb.add(button_unban_user)

            await message.answer(f"Привет! {message.from_user.first_name}! \n"
                                 f"Открой меню в правом нижнем углу, чтобы получить доступ ко всем функциям.",
                                 parse_mode=ParseMode.HTML, reply_markup=greet_kb
                                 )
        else:
            await DialogueStates.registration.set()
            await message.answer(f"Вам необходимо пройти регистрацию. "
                                 f"Введите свои данные в соответствии со следующей формой: "
                                 f"Имя Фамилия Комната."
                                )

    @staticmethod
    @dp.message_handler(commands=['help'])
    async def help_command(message: Message):
        await message.answer(f"Привет! Я создан, чтобы помогать тебе, сделать твою жизнь в общежитии комфортнее."
                             f" Все команды доступны из меню, открыть которое можно из панели клавиатуры "
                             f"в правом нижнем углу. Чтобы меню появилось, необходимо написать мне \"/start\","
                             f" если ты конечно еще не сделал этого ранее.")

    @staticmethod
    @dp.message_handler(state='*', content_types=['photo', 'text'], )
    async def message_handler(message: Message):

        try:
            await DormBot.dp.throttle('start', rate=0.2)
        except Throttled:
            await message.reply('Слишком часто пишешь! Не дудос ли это часом? --_--')
            return 0

        if (message.text == str(DormBot.admin_password)) & (not(DormBot.admin_password == 0)):
            DormBot.admin_password = 0
            DormBot.db_connection.add_admin(message.from_user.id)
            return await message.answer(f"Вы теперь админ. Введите \n"
                                        f"/start\n"
                                        f"чтобы расширить свое меню."
                                        )

        state = DormBot.dp.current_state(user=message.from_user.id)
        state_name = await state.get_state()
        if (not DormBot.db_connection.select_users(user_id=message.from_user.id)) and \
                (not (state_name == 'DialogueStates:registration')):
            await DialogueStates.registration.set()
            return await message.answer(f"Вам необходимо пройти регистрацию. "
                                        f"Введите свои данные в соответствии со следующей формой: "
                                        f"Имя Фамилия Комната."
                                        )

        msg = UserMessage(message, state, DormBot.bot, DormBot.db_connection, DormBot.default_answers)
        await msg.message_parse()

        if msg.admin_password:
            DormBot.admin_password = msg.admin_password
        if msg.output:
            await msg.message.reply(msg.output, reply=False)
        if msg.media:
            await msg.bot.send_photo(msg.user_id, msg.media)
        if msg.inline_kb:
            await msg.message.answer(msg.inline_kb_text, reply_markup=msg.inline_kb)

        return 0

    @staticmethod
    @dp.callback_query_handler()
    async def inline_callback(callback_query: CallbackQuery):
        state = DormBot.dp.current_state(user=callback_query.from_user.id)
        callback = Callbacks(callback_query, state, DormBot.db_connection)
        await callback.process()
        await DormBot.bot.answer_callback_query(callback_query.id)
        await DormBot.bot.send_message(callback_query.from_user.id, callback.output)

    @staticmethod
    async def shutdown(dispatcher: Dispatcher):
        await dispatcher.storage.close()
        await dispatcher.storage.wait_closed()

    @staticmethod
    def repeat(coro, loop):
        asyncio.ensure_future(coro(), loop=loop)
        loop.call_later(DormBot.message_delay, DormBot.repeat, coro, loop)

    @staticmethod
    async def send_to_administration():

        try:
            question_row = DormBot.db_connection.get_last_queued_question()
            question_id = question_row[0][0]
            user_id = question_row[0][1]
            question_text = question_row[0][2]

            user_row = DormBot.db_connection.select_users(user_id=user_id)
            user_name = user_row[0][1]
            user_surname = user_row[0][2]
            user_room = user_row[0][4]

        except Exception as ex:
            return 0

        question_text = str(question_id) + ' ' + user_name + ' ' + \
                        user_surname + ' ' + str(user_room) + '\n' + question_text

        await DormBot.bot.send_message(chat_id=-523185281, text=question_text)
        DormBot.db_connection.update_question(question_id=question_id, status='processing')


if __name__ == '__main__':
    bot = DormBot()
