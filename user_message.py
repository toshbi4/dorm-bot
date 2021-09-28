import random

from aiogram import Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, ContentType
from utils import DialogueStates
from db import DBConnection


class UserMessage:
    text = ''
    user_id = 0
    state = None
    bot = None
    output = ''
    media = None
    default_answers = []
    inline_kb = None
    inline_kb_text = ''
    swearing = []
    super_admin_id = 0
    admin_password = 0

    def __init__(self, message: Message, state: FSMContext, bot: Bot, db_connection: DBConnection, default_answers):

        self.state = state
        self.user_id = message.from_user.id
        self.bot = bot
        self.message = message
        self.db_connection = db_connection
        self.default_answers = default_answers

        if message.text:
            self.text = message.text
        elif message.caption:
            self.text = message.caption
        elif message.caption_entities:
            self.text = message.caption_entities

        f = open("cfg/swearing.txt", "r")
        self.swearing = f.read().split()
        f.close()

        f = open("cfg/admin_id.txt", "r")
        self.super_admin_id = f.read()
        f.close()

    async def message_parse(self):

        try:
            user_group = self.db_connection.select_users(user_id=self.user_id)[0][3]
        except:
            user_group = 'newbee'

        for sw in self.swearing:
            if not(self.text.find(sw) == -1):
                self.media = InputFile('imgs/swearing.jpg')
                return 0

        print(self.admin_password)

        if self.text == 'Хочу спросить.':
            await DialogueStates.question.set()
            self.output = 'Напиши, пожалуйста, текст вопроса.'

        elif self.text == 'Хочу оставить заявку.':
            await DialogueStates.request.set()
            self.output = 'Напиши, пожалуйста, текст заявки в формате:\n' \
                          'Кому (электрику/сантехнику/плотнику)\n' \
                          'Место (комната 2222/вторая кабинка, туалет, 3й блок, 10 этаж)\n' \
                          'Ситуация (фонтан невероятной красоты прямиком из унитаза)'
        elif self.text == 'Есть идея/пожелание/предложение.':
            await DialogueStates.idea.set()
            self.output = 'Напишите, пожалуйста, текст вашего предложения. ' \
                          'Он будет отправлен администрации для рассмотрения'
        elif self.text == 'Добавить стандартный вопрос.' and user_group == 'admin':
            await DialogueStates.add_default_question.set()
            self.output = 'Укажите данные для стандартного вопроса в формате: ' \
                          '"<ключевые слова>,' \
                          '<текст>". Также к соощению можно приложить одно фото, которое отобразится в ответе.'
        elif self.text == 'Удалить стандартный вопрос.' and user_group == 'admin':
            await DialogueStates.del_default_question.set()
            answers_list = ''
            for answer in self.default_answers:
                answers_list += str(answer[0]) + '  '
                answers_list += str(answer[1]) + '  '
                answers_list += '\n'
            self.output = ' Выберите id ответа, который хотите удалить: \n' + answers_list

        elif self.text == 'Случайное число.' and user_group == 'super_admin':
            self.admin_password = random.randint(1000, 9999)
            self.output = self.admin_password
            return 0
        else:
            await self.state_handler()

    async def state_handler(self):
        state_name = await self.state.get_state()

        if state_name == 'DialogueStates:question':
            await self.question_state()
        elif state_name == 'DialogueStates:request':
            await self.request_state()
        elif state_name == 'DialogueStates:idea':
            await self.idea_state()
        elif state_name == 'DialogueStates:registration':
            await self.registration_state()
        elif state_name == 'DialogueStates:add_default_question':
            await self.add_default_question_state()
        elif state_name == 'DialogueStates:del_default_question':
            await self.del_default_question_state()
        else:
            if not self.message.chat.type == 'group':
                self.output = 'Выбери действиe в меню из нижней части диалога.'
            else:
                if self.message.reply_to_message.text:
                    await self.handle_replied_answer()

    async def handle_replied_answer(self):
        replied_text = self.message.reply_to_message.text
        self.output = 'Ответ был успешно отправлен!'

        msg_id = replied_text.split()[0]
        msg_text = self.db_connection.get_question(msg_id)[0][2]
        user_id = self.db_connection.get_question(msg_id)[0][1]

        self.text = "Ответ на ваше сообщение: \n \n" + msg_text
        await self.message.forward(user_id)
        await self.bot.send_message(chat_id=user_id, text=self.text)
        return self.db_connection.del_question(msg_id)

    async def question_state(self):

        await self.state.reset_state()

        for answer in self.default_answers:
            key_words = answer[1].split()
            accept_answer = True
            for word in key_words:
                if self.text.lower().find(word) == -1:
                    accept_answer = False
            if accept_answer:
                if not answer[2] == '':
                    self.media = InputFile(answer[2])
                if not answer[3] == '':
                    self.output = answer[3]

                await self.state.update_data(question=self.text)

                # keyboards.py
                inline_btn_1 = InlineKeyboardButton('Да :)', callback_data='qst_yes')
                inline_btn_2 = InlineKeyboardButton('Нет :( Перенаправить мой вопрос администрации.',
                                                    callback_data='qst_no')
                inline_kb1 = InlineKeyboardMarkup().row(inline_btn_1)
                inline_kb1.add(inline_btn_2)
                self.inline_kb = inline_kb1
                self.inline_kb_text = 'Я ответил на Ваш вопрос?'
                return 0

        # keyboards.py
        inline_btn_1 = InlineKeyboardButton('Ок', callback_data='agree')
        inline_btn_2 = InlineKeyboardButton('Не ок', callback_data='disagree')
        inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1, inline_btn_2)
        self.inline_kb = inline_kb1
        self.inline_kb_text = 'Перенаправить Ваш вопрос администрации?.'
        await self.state.update_data(question=self.text)

    async def request_state(self):
        self.db_connection.add_question(self.state.chat, self.text)
        await self.state.reset_state()
        self.output = 'Ваша заявка успешно принята.'

    async def idea_state(self):
        self.db_connection.add_question(self.state.chat, self.text)
        await self.state.reset_state()
        self.output = 'Ваше предложение успешно отправлено ' \
                      'администрации для рассмотрения.'

    async def registration_state(self):
        user_data = self.text.split()
        if self.db_connection.select_users(user_id=self.user_id):
            await self.state.reset_state()
            self.output = 'Вы уже зарегистрированы. Добро пожаловать.'
        user_group = 'user'

        if int(self.super_admin_id) == int(self.user_id):
            user_group = 'super_admin'

        if len(user_data) == 3:
            self.db_connection.add_user(self.user_id,
                                        user_data[0],
                                        user_data[1],
                                        user_group,
                                        int(user_data[2]))

            await self.state.reset_state()
            self.output = 'Вы были успешно зарегистрированы! ' \
                          'Добро пожаловать!'
        else:
            self.output = 'Ошибка введенных данных. \n' \
                          'Введите, пожалуйста, свои данные в соответствии с формой: \n' \
                          'Имя Фамилия Комната.'

    async def add_default_question_state(self):
        default_answer = self.text.split(',')
        if len(default_answer) >= 2:

            photo_path = ''
            if self.message.content_type == ContentType.PHOTO:

                try:
                    count = str(self.default_answers[-1][0] + 1)
                except:
                    count = '0'

                photo_path = 'imgs/' + count
                await self.message.photo[-1].download(photo_path)

            self.db_connection.add_answer(default_answer[0],
                                          photo_path,
                                          default_answer[1].strip())
            answer_id = 0
            if len(self.default_answers) > 0:
                answer_id = self.default_answers[len(self.default_answers) - 1][0] + 1

            self.default_answers.append((answer_id,
                                         default_answer[0],
                                         photo_path,
                                         default_answer[1].strip()))

        self.output = 'Добавил новый стандартный ответ.'
        await self.state.reset_state()

    async def del_default_question_state(self):
        try:
            self.db_connection.del_answers(int(self.text))
            self.output = 'Удалил стандартный ответ с id = ' + self.text
            await self.state.reset_state()

            for answer in self.default_answers:
                if answer[0] == int(self.text):
                    self.default_answers.remove(answer)
                    break

        except Exception as ex:
            self.output = 'Неверный формат ввода. Введите, пожалуйста, id ответа, ' \
                          'который хотите удалить, числом.'
            print(ex)

    def save_question_to_queue(self):
        pass
