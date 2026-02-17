import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers.start import router as start_router
from handlers.booking import router as booking_router

async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage()) # хранилище состояний FSM прямо в оперативной памяти. Для продакшна используют RedisStorage — там состояния сохраняются даже после перезапуска.

    dp.include_router(start_router)
    dp.include_router(booking_router)

    print("Бот запущен!")
    await dp.start_polling(bot)

asyncio.run(main())


