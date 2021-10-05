from aiogram.dispatcher.filters.state import State, StatesGroup


class DialogueStates(StatesGroup):

    base = State()
    idea = State()
    question = State()
    sending = State()
    request = State()
    registration = State()
    add_default_question = State()
    del_default_question = State()
    ban_user = State()
    unban_user = State()
    del_user = State()
