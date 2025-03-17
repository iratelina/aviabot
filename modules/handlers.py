from aiogram import types, Dispatcher
from aiogram.filters import Command
from modules.keyboards import keyboard
from modules.api import get_iata_code, get_popular_directions, get_tickets
from config import MONTHS
import asyncio
from datetime import datetime
from logger import logger

dp = Dispatcher()

user_data = {}

# Стартовая команда
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer('Привет! Я - бот, который поможет в поиске авиабилетов. Нажмите кнопку "Помощь" или выполните команду /help , если хотите узнать, как пользоваться ботом', reply_markup=keyboard)

# Обработка команды и нажатия кнопки "Помощь"
@dp.message(Command('help'))
@dp.message(lambda message: message.text == 'Помощь')
async def help (message: types.Message):
    await message.answer('Для работы с ботом можно использовать команды или кнопки.\n'
        'Доступные команды:\n'
        '/start — приветствие\n'
        '/help — список команд\n'
        '/find_tickets — поиск билетов\n'
        '/popular_directions — список популярных направлений перелётов'
    )

# Обработка команды и нажатия кнопки "Популярные направления"
@dp.message(Command('popular_directions'))
@dp.message(lambda message: message.text == 'Популярные направления')
async def get_directions(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    user_data[user_id]['step'] = 'popular_directions'
    await message.answer('Введите название города, чтобы узнать популярные направления ✈️')

# Обработка команды и нажатия кнопки "Искать билеты"
@dp.message(Command('find_tickets'))
@dp.message(lambda message: message.text == 'Искать билеты')
async def find_tickets(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    await message.answer('Сейчас бот задаст несколько вопросов о городе отправления, пункте назначения и интересующем Вас месяце для путешествия. Затем он найдёт и предложит доступные рейсы за весь указанный период с указанием цен. Чтобы получить наиболее точные результаты, отвечайте чётко и проверяйте корректность Вашего запроса')
    await asyncio.sleep(3)
    await message.answer('Отлично, начнем поиск! ✈️  Из какого города Вы летите?')
    user_data[user_id]['step'] = 'origin'

# Обработка неизвестьных команд
@dp.message(lambda message: message.text.startswith('/'))
async def unknown_command(message: types.Message):
    logger.error('Неизвестная команда')
    await message.answer('❌ Неизвестная команда. Напишите /help для списка доступных команд')
    
# Обработка сообщений
@dp.message()
async def get_info(message: types.Message):
    user_id = message.from_user.id
    step = user_data[user_id].get('step')
    if step == 'popular_directions':
        city_name = message.text
        iata_code_origin = get_iata_code(city_name)
        if not iata_code_origin:
            logger.warning(f'Город "{city_name}" не найден')
            await message.answer('❌ Город не найден. Попробуйте ввести другое название')
            return
        await message.answer('🔍 Ищу направления...')
        directions = get_popular_directions(iata_code_origin)
        await message.answer(directions)
        user_data[user_id]['step'] = None
        return

    elif step == 'origin':
        origin = message.text
        iata_code_origin = get_iata_code(origin)
        if not iata_code_origin:
            logger.warning(f'Город "{origin}" не найден')
            await message.answer('❌ Ошибка! Возможно в запросе допущена опечатка, или в указанном городе нет аэропорта. Попробуйте еще раз ввести название города')
            return
        user_data[user_id]['origin'] = origin
        user_data[user_id]['iata_code_origin'] = iata_code_origin
        await message.answer('Хорошо! Куда направляетесь?')
        user_data[user_id]['step'] = 'destination'
        return

    elif step == 'destination':
        destination = message.text
        if destination == user_data[user_id]['origin']:
            logger.warning(f'Города отправления и прибытия совпадают')
            await message.answer ('❌ Ошибка! Город отправления и пункт назначения должны различаться. Введите другой город')
            return
        user_data[user_id]['destination'] = message.text
        iata_code_destination = get_iata_code(message.text)
        if not iata_code_destination:
            logger.warning(f'Город "{destination}" не найден')
            await message.answer ('❌ Ошибка! Возможно, в запросе допущена опечатка, или в указанном городе нет аэропорта. Попробуйте еще раз ввести название города')
            return
        user_data[user_id]['iata_code_destination'] = iata_code_destination
        await message.answer('📅 В каком месяце Вы планируете полёт? Напишите название месяца или его числовое обозначение (например, Март или 03)')
        user_data[user_id]['step'] = 'date'
        return

    else:
        current_year = datetime.now().year
        month = message.text
        if month.isdigit():
            if int(month) < 1 or int(month) > 12:
                logger.warning(f'Некорректно введен номер месяца: {month}')
                await message.answer('❌ Ошибка! Введите корректный номер месяца (от 01 до 12)')
                return
        elif month in MONTHS:
            month = MONTHS[month]
        else:
            logger.warning(f'Некорректно введено название месяца: {month}')
            await message.answer('❌ Ошибка! Введите корректное название или номер месяца (от 01 до 12)')
            return
        formatted_date = f'{current_year}-{month}-01'
        user_data[user_id]['date'] = formatted_date
        origin = user_data[user_id]['origin']
        destination = user_data[user_id]['destination']
        date = user_data[user_id]['date']
        iata_code_origin = user_data[user_id]['iata_code_origin']
        iata_code_destination = user_data[user_id]['iata_code_destination']
        await message.answer(f'📍 Маршрут: {iata_code_origin} → {iata_code_destination}\n🔍 Ищу билеты...')

        tickets_info = get_tickets(iata_code_origin, iata_code_destination, date)
        await message.answer(tickets_info)
        await message.answer('Выберите следующую команду')
