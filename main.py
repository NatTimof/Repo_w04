import asyncio
from datetime import datetime, timedelta
import sys
import logging
from pprint import pprint as print

from aiohttp import ClientSession, ClientConnectorError


def get_url(date):
    return f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date.strftime("%d.%m.%Y")}'

async def request(url: str):
    async with ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.ok:
                    r = await resp.json()
                    return r
                logging.error(f"Error status: {resp.status} for {url}")
                return None
        except ClientConnectorError as err:
            logging.error(f"Connection error: {str(err)}")
            return None

def extract_rates(data, currencies=['USD', 'EUR']):
    if not data or 'exchangeRate' not in data:
        return {}
    rates = {}
    for entry in data['exchangeRate']:
        if entry.get('currency') in currencies:
            rates[entry['currency']] = {'purchase': entry.get('purchaseRate'), 'sale': entry.get('saleRate')}
    return rates

async def get_exchange_rates(days):
    start_date = datetime.now().date() - timedelta(days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    urls = [get_url(date) for date in dates]

    async with ClientSession() as session:
        tasks = [request(url) for url in urls]
        results = await asyncio.gather(*tasks)

    rates_list = []
    for result, date in zip(results, dates):
        rates_dict = extract_rates(result)
        if rates_dict:
            rates_list.append({date.strftime("%d.%m.%Y"): rates_dict})
    return rates_list

def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Usage: py main.py <number_of_days>")
        return

    days = int(sys.argv[1])
    if not 1 <= days <= 10:
        print("Number of days should be between 1 and 10.")
        return

    rates = asyncio.run(get_exchange_rates(days))
    print(rates)


if __name__ == '__main__':
    main()