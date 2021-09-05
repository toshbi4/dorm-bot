import datetime

from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from db import DBConnection


class Callbacks:
    callback_query = None
    output = ''
    state = None

    def __init__(self, callback_query: CallbackQuery, state: FSMContext, db_connection: DBConnection):
        self.callback_query = callback_query
        self.state = state
        self.db_connection = db_connection

    async def process(self):
        if self.callback_query.data.startswith('qst_yes'):
            await self.callback_yes_btn()
        elif self.callback_query.data.startswith('qst_no'):
            await self.callback_no_btn()
        elif self.callback_query.data.startswith('agree'):
            await self.callback_agree_btn()
        elif self.callback_query.data.startswith('disagree'):
            await self.callback_disagree_btn()

    async def callback_yes_btn(self):
        self.output = 'Приятно быть полезным!'

    async def callback_no_btn(self):
        user_data = await self.state.get_data()
        print(self.state.chat)
        print(user_data['question'])
        self.output = 'Виноват. Ваш вопрос перенаправлен администрации.'

    async def callback_agree_btn(self):
        user_data = await self.state.get_data()
        print(self.state.chat)
        print(user_data['question'])
        self.db_connection.add_question(self.state.chat, user_data['question'])
        self.output = 'Ваш вопрос перенаправлен администрации.'

    async def callback_disagree_btn(self):
        self.output = 'Отбой.'
