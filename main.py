import logging
import re
from utils import TestStates

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, \
    Message, ParseMode, CallbackQuery, InputFile


class DormBot:
    f = open("bot_token.txt", "r")
    bot_token = f.read().strip()
    f.close()

    # Initialize bot and dispatcher
    bot = Bot(token=bot_token)
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(LoggingMiddleware())

    def __init__(self):

        executor.start_polling(self.dp, on_shutdown=DormBot.shutdown, skip_updates=True)

    @staticmethod
    @dp.message_handler(state='*', text=['Хочу спросить.'])
    async def question(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)

        await state.set_state(TestStates.all()[2])
        await message.reply('Напиши, пожалуйста, текст вопроса.', reply=False)

    @staticmethod
    @dp.message_handler(state='*', text=['Хочу оставить заявку.'])
    async def request(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)

        await state.set_state(TestStates.all()[3])
        await message.reply('Напиши, пожалуйста, текст заявки в формате:\n'
                            'Кому (электрику/сантехнику/плотнику)\n'
                            'Место (комната 2222/вторая кабинка, туалет, 3й блок, 10 этаж)\n'
                            'Ситуация (фонтан невероятной красоты прямиком из унитаза)', reply=False)

    @staticmethod
    @dp.message_handler(state='*', text=['Есть идея/пожелание/предложение.'])
    async def question(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)

        await state.set_state(TestStates.all()[1])
        await message.reply('Напишите, пожалуйста, текст вашего предложения. '
                            'Он будет отправлен администрации для рассмотрения', reply=False)

    @staticmethod
    @dp.message_handler(state=TestStates.QUESTION)
    async def first_test_state_case_met(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)

        question = message.text.lower()

        await state.reset_state()

        if not question.find('расписан') == -1:
            if not question.find('душ') == -1:
                showerPhoto = InputFile("shower.jpg")
                await DormBot.bot.send_photo(message.from_user.id, showerPhoto)
            elif not question.find('прачечн') == -1:
                await message.reply('Расписание прачечной.')
            else:
                return await message.reply('Такой комнаты нет в моей базе.'
                                           'Попробуйте, например: "расписание душа"')
        elif not question.find('осмотр') == -1:
            osmotrPhoto = InputFile("osmotr.jpg")
            await DormBot.bot.send_photo(message.from_user.id, osmotrPhoto)

        # keyboards.py
        inline_btn_1 = InlineKeyboardButton('Да :)', callback_data='qst_yes')
        inline_btn_2 = InlineKeyboardButton('Нет :(', callback_data='qst_no')
        inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1, inline_btn_2)

        return await message.answer('Я ответил на ваш вопрос? \n---\n\"' + message.text + '\"',
                                   reply_markup=inline_kb1)

    @staticmethod
    @dp.message_handler(state=TestStates.REQUEST)
    async def second_test_state_case_met(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)
        await state.reset_state()
        return await message.reply('Ваша заявка успешно принята.')

    @staticmethod
    @dp.message_handler(state=TestStates.IDEA)
    async def third_test_state_case_met(message: Message):
        state = DormBot.dp.current_state(user=message.from_user.id)
        await state.reset_state()
        return await message.reply('Ваше предложение успешно отправлено '
                                   'администрации для рассмотрения.')

    @staticmethod
    @dp.callback_query_handler(lambda c: c.data.startswith('qst_yes'))
    async def process_callback_button1(callback_query: CallbackQuery):
        await DormBot.bot.answer_callback_query(callback_query.id)
        await DormBot.bot.send_message(callback_query.from_user.id, 'Приятно быть полезным!')

    @staticmethod
    @dp.callback_query_handler(lambda c: c.data.startswith('qst_no'))
    async def process_callback_button2(callback_query: CallbackQuery):
        sent_qst = callback_query.message.text
        print(sent_qst.split('---\n')[1])
        await DormBot.bot.answer_callback_query(callback_query.id)
        await DormBot.bot.send_message(callback_query.from_user.id, 'Виноват. Ваш вопрос будет перенаправлен '
                                                                    'администрации и на него ответит человек.')

    @staticmethod
    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: Message):
        """
        This handler will be called when user sends `/start` or `/help` command
        """

        button_questions = KeyboardButton('Хочу спросить.')
        button_request = KeyboardButton('Хочу оставить заявку.')
        button_idea = KeyboardButton('Есть идея/пожелание/предложение.')
        greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        greet_kb.add(button_questions)
        greet_kb.add(button_request)
        greet_kb.add(button_idea)

        await message.answer(f"Привет! {message.from_user.first_name}! 👋",
                             parse_mode=ParseMode.HTML, reply_markup=greet_kb
                             )

    @staticmethod
    @dp.message_handler(state='*')
    async def some_test_state_case_met(message: Message):
        await message.reply('Выбери действиe в меню из нижней части диалога.', reply=False)

    @staticmethod
    async def shutdown(dispatcher: Dispatcher):
        await dispatcher.storage.close()
        await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    bot = DormBot()
