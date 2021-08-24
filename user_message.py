from aiogram import Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from utils import DialogueStates
from db import DBConnection


class UserMessage:
    text = ''
    user_id = 0
    state = None
    bot = None
    output = ''
    media = None

    def __init__(self, message: Message, state: FSMContext, bot: Bot, db_connection: DBConnection):

        self.state = state
        self.text = message.text
        self.user_id = message.from_user.id
        self.bot = bot
        self.message = message
        self.db_connection = db_connection

    async def message_parse(self):
        state_name = await self.state.get_state()

        if self.text == 'Хочу спросить.':
            await DialogueStates.question.set()
            self.output = 'Напиши, пожалуйста, текст вопроса.'
            return 0
        elif self.text == 'Хочу оставить заявку.':
            await DialogueStates.request.set()
            self.output = 'Напиши, пожалуйста, текст заявки в формате:\n' \
                          'Кому (электрику/сантехнику/плотнику)\n' \
                          'Место (комната 2222/вторая кабинка, туалет, 3й блок, 10 этаж)\n' \
                          'Ситуация (фонтан невероятной красоты прямиком из унитаза)'
            return 0
        elif self.text == 'Есть идея/пожелание/предложение.':
            await DialogueStates.idea.set()
            self.output = 'Напишите, пожалуйста, текст вашего предложения. ' \
                          'Он будет отправлен администрации для рассмотрения'
            return 0

        if state_name == 'DialogueStates:question':
            await self.question_state()
        elif state_name == 'DialogueStates:request':
            await self.request_state()
        elif state_name == 'DialogueStates:idea':
            await self.idea_state()
        elif state_name == 'DialogueStates:registration':
            await self.registration_state()
        else:
            self.output = 'Выбери действиe в меню из нижней части диалога.'

    async def question_state(self):

        await self.state.reset_state()

        if not self.text.lower().find('расписан') == -1:
            if not self.text.lower().find('душ') == -1:
                self.media = InputFile("shower.jpg")
            elif not self.text.lower().find('прачечн') == -1:
                self.output = 'Расписание прачечной.'
            else:
                self.output = 'Такой комнаты нет в моей базе.' \
                              'Попробуйте, например: "расписание душа"'
                return 0

        elif not self.text.lower().find('осмотр') == -1:
            self.media = InputFile("osmotr.jpg")
        else:
            # keyboards.py
            inline_btn_1 = InlineKeyboardButton('Ок', callback_data='agree')
            inline_btn_2 = InlineKeyboardButton('Не ок', callback_data='disagree')
            inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1, inline_btn_2)
            await self.state.update_data(question=self.text)
            return await self.message.answer('Ваш вопрос будет отправлен администрации. Ок?',
                                             reply_markup=inline_kb1)

        await self.state.update_data(question=self.text)

        # keyboards.py
        inline_btn_1 = InlineKeyboardButton('Да :)', callback_data='qst_yes')
        inline_btn_2 = InlineKeyboardButton('Нет :( Перенаправить мой вопрос администрации.',
                                            callback_data='qst_no')
        inline_kb1 = InlineKeyboardMarkup().row(inline_btn_1)
        inline_kb1.add(inline_btn_2)

        return await self.message.answer('Я ответил на ваш вопрос?', reply_markup=inline_kb1)

    async def request_state(self):
        await self.state.reset_state()
        self.output = 'Ваша заявка успешно принята.'

    async def idea_state(self):
        await self.state.reset_state()
        self.output = 'Ваше предложение успешно отправлено ' \
                      'администрации для рассмотрения.'

    async def registration_state(self):
        user_data = self.text.split()
        if self.db_connection.select_users(user_id=self.user_id):
            await self.state.reset_state()
            self.output = 'Вы уже зарегистрированы. Добро пожаловать.'
        if len(user_data) == 4:
            self.db_connection.add_user(self.user_id,
                                        user_data[0],
                                        user_data[1],
                                        user_data[2],
                                        int(user_data[3]))

            await self.state.reset_state()
            self.output = 'Вы были успешно зарегистрированы! ' \
                          'Добро пожаловать!'
        else:
            self.output = 'Ошибка введенных данных.'

    def send_to_administration(self):
        pass
