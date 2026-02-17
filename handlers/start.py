from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import SERVICES

router = Router()

@router.message(Command('start'))
async def start(message: Message):
    # Создаем кнопки с услугами
    buttons =  [[KeyboardButton(text=service)] for service in SERVICES.keys()]
    buttons.append([KeyboardButton(text="❌ Отмена")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True, # кнопки нормального размера
    )

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Выберите услугу для записи:",
        reply_markup=keyboard
    )