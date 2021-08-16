from aiogram.utils.helper import Helper, HelperMode, ListItem


class TestStates(Helper):
    mode = HelperMode.snake_case

    BASE = ListItem()
    IDEA = ListItem()
    QUESTION = ListItem()
    REQUEST = ListItem()
