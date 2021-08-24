from aiogram.dispatcher.filters.state import State, StatesGroup


class DialogueStates(StatesGroup):

    base = State()
    idea = State()
    question = State()
    sending = State()
    request = State()
    registration = State()
