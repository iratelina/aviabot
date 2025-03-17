import requests
from config import TRAVELPAYOUTS_API_TOKEN
from logger import logger
from datetime import datetime

def get_iata_code(city_name):
    url = 'https://autocomplete.travelpayouts.com/places2'
    params = {
        'term': city_name,
        'locale': 'ru',
        'types': 'city',
        'token': TRAVELPAYOUTS_API_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0 and 'code' in data[0]: 
            iata_code = data[0]['code']
            logger.info(f'Код ответа: {response.status_code}. Данные получены')
            return iata_code
        else:
            logger.warning(f'IATA-код не найден для "{city_name}"')
            return None
    else:
        logger.error(f'Код ответа: {response.status_code}. Ошибка API: {response.text}')
        return None

def get_city_by_iata(iata_input):
    url = 'https://autocomplete.travelpayouts.com/places2'
    cities = []

    if isinstance(iata_input, str):
        iata_input = [iata_input]

    for iata_code in iata_input:
        params = {
            'term': iata_code,
            'locale': 'ru',
            'types': 'city',
            'token': TRAVELPAYOUTS_API_TOKEN
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            cities.append(data[0]['name'])
            logger.info(f'Код ответа: {response.status_code}. Данные получены')
        else:
            logger.error(f'Код ответа: {response.status_code}. Ошибка API: {response.text}')
            return None
    return cities[0] if len(cities) == 1 else cities
            

def get_popular_directions(iata_code_origin):
    url = 'https://api.travelpayouts.com/v1/city-directions'
    params = {
        'currency':	'RUB',
        'origin': iata_code_origin,
        'token': TRAVELPAYOUTS_API_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        iata_codes = [key for key, value in data['data'].items()]
        logger.info(f'Код ответа: {response.status_code}. Данные получены')
        cities_names = get_city_by_iata(iata_codes[:10])
        origin = get_city_by_iata(iata_code_origin)
        cities_list = []
        for name in cities_names:
            route = f'📍 {origin} → {name}'
            cities_list.append(route)
        logger.info('Сообщение о самых популярных направлениях отправлено')
        return 'Самые популярные направления:\n\n' + '\n'.join(cities_list)
    else:
        logger.error(f'Код ответа: {response.status_code}. Ошибка API: {response.text}')
        return None

def get_tickets(iata_code_origin, iata_code_destination, date):
    url = 'https://api.travelpayouts.com/v2/prices/month-matrix'
    params = {
        'currency': 'RUB',
        'origin': iata_code_origin,
        'destination': iata_code_destination,
        'month': date,
        'show_to_affiliates': 'true',
        'token': TRAVELPAYOUTS_API_TOKEN
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        tickets = []
        count = 0
        if 'data' in data and data['data'] and len(data['data']) > 0:
            sorted_tickets = sorted(data['data'], key=lambda x: x['depart_date'])
            ticket = data['data'][0]
            price = ticket['value']
            logger.info(f'Код ответа: {response.status_code}. Данные получены')
            for ticket in sorted_tickets:
                price = ticket['value']
                gate = ticket['gate']
                departure_at = ticket['depart_date']
                formatted_date = datetime.strptime(f'{departure_at}', "%Y-%m-%d").strftime("%d.%m.%Y")
                flight_info = f'💰 Цена: {price} RUB\n Дата вылета: {formatted_date}✈️\n' + (f'Источник: {gate}' if gate else '')
                tickets.append(flight_info + '\n')
                count += 1
            logger.info('Сообщение об авиабилетах отправлено')
            return f'🎟 Найдено {count} авиабилетов за указанный месяц:\n\n' + '\n'.join(tickets)
        else:
            logger.info('Сообщение отправлено')
            return '❌ К сожалению, билеты за указанный период не найдены. Попробуйте другое направление или месяц'
    else:
        logger.error(f'Код ответа: {response.status_code}. Ошибка API: {response.text}')
        return None