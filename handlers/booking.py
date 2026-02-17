from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import SERVICES, TIME_SLOTS, ADMIN_ID
from database import save_booking

router = Router()


# FSM — машина состояний
# Это как сессия пользователя, запоминает на каком шаге он находится
class BookingStates(StatesGroup):
    choosing_service = State()  # ждём выбор услуги
    choosing_time = State()  # ждём выбор времени
    confirming = State()  # ждём подтверждение


# Шаг 1 — пользователь выбрал услугу
@router.message(F.text.in_(SERVICES.keys()))
async def service_chosen(message: Message, state: FSMContext):
    service = message.text
    price_info = SERVICES[service]

    # Сохраняем выбор в состояние
    # state.update_data() — сохраняем данные в "сессию" пользователя
    # Это как session.setAttribute() в Java
    # Данные живут пока пользователь не завершит диалог
    await state.update_data(service=service)

    # Переводим пользователя в следующее состояние
    # Теперь следующее сообщение от него попадёт в handler
    # который слушает BookingStates.choosing_time
    await state.set_state(BookingStates.choosing_time)

    # Кнопки со временем
    buttons = []
    row = []
    for i, slot in enumerate(TIME_SLOTS):
        row.append(KeyboardButton(text=slot))
        if len(row) == 3:  # по 3 кнопки в ряд
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text="❌ Отмена")])

    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer(
        f"✅ Услуга: {service}\n"
        f"💰 Цена: {price_info}\n\n"
        "Выберите удобное время:",
        reply_markup=keyboard
    )


# Шаг 2 — пользователь выбрал время
# Двойной фильтр:
# 1) пользователь должен быть в состоянии choosing_time
# 2) текст должен быть одним из TIME_SLOTS
# Если пользователь не в этом состоянии — handler не сработает
@router.message(BookingStates.choosing_time, F.text.in_(TIME_SLOTS))
async def time_chosen(message: Message, state: FSMContext):
    time_slot = message.text

    # state.get_data() — достаём сохранённые данные
    # Это как session.getAttribute() в Java
    data = await state.get_data()
    service = data["service"]  # то что сохранили на шаге 1

    await state.update_data(time_slot=time_slot)
    await state.set_state(BookingStates.confirming)

    # Кнопки подтверждения
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"📋 Проверьте запись:\n\n"
        f"💇 Услуга: {service}\n"
        f"🕐 Время: {time_slot}\n\n"
        "Всё верно?",
        reply_markup=keyboard
    )


# Шаг 3 — пользователь подтвердил
@router.message(BookingStates.confirming, F.text == "✅ Подтвердить")
async def booking_confirmed(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    service = data["service"]
    time_slot = data["time_slot"]

    username = message.from_user.username or "без username"
    user_id = message.from_user.id

    # Сохраняем в базу
    await save_booking(user_id, username, service, time_slot)

    # Уведомляем администратора
    await bot.send_message(
        ADMIN_ID,
        f"🔔 Новая запись!\n\n"
        f"👤 Клиент: @{username} (id: {user_id})\n"
        f"💇 Услуга: {service}\n"
        f"🕐 Время: {time_slot}"
    )

    # Отвечаем пользователю
    await message.answer(
        f"🎉 Готово! Вы записаны.\n\n"
        f"💇 Услуга: {service}\n"
        f"🕐 Время: {time_slot}\n\n"
        "Ждём вас! Если нужно отменить — напишите нам.",
        reply_markup=ReplyKeyboardRemove()
    )

    # Сбрасываем состояние
    await state.clear()


# Отмена на любом шаге
@router.message(F.text == "❌ Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Запись отменена. Напишите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )