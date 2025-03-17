from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Помощь')],
        [KeyboardButton(text='Искать билеты')],
        [KeyboardButton(text='Популярные направления')]
    ],
    resize_keyboard=True
)
