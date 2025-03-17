import asyncio
from aiogram import Bot
from config import BOT_TOKEN
from modules.handlers import dp 
from logger import logger

bot = Bot(token=BOT_TOKEN)

async def main():
    logger.info('Бот успешно запущен')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f'Ошибка в работе бота: {e}', exc_info=True)
