"""Module creating a test FastAPI app"""
import statistics
import time
import requests

from fastapi import FastAPI

app = FastAPI()

urls = [
    'https://api1.com',
    'https://api2.com',
    'https://api3.com',
]

@app.get('/{member_id}')
async def root(member_id: int):
    """Function that handles a GET request to the root URL"""
    oop_max_list = []
    remaining_oop_max_list = []
    copay_list = []

    for url in urls:
        url = f'{url}?member_id={member_id}'
        member_data = get_member_data(url, member_id)
        try:
            oop_max_list.append(member_data['oop_max'])
            remaining_oop_max_list.append(member_data['remaining_oop_max'])
            copay_list.append(member_data['copay'])
        except TypeError as e:
            print(e)
            print(f'url: {url}')

    oop_max = get_formatted_mode(oop_max_list)
    remaining_oop_max = get_formatted_mode(remaining_oop_max_list)
    copay = get_formatted_mode(copay_list)

    return {'oop_max': oop_max, 'remaining_oop_max': remaining_oop_max, 'copay': copay}

def get_member_data(url: str, member_id: int, max_retries=3, retry_delay=1):
    """Function that calls external API for member data with retry logic"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params={'member_id': member_id}, timeout=5)
            resp.raise_for_status()
            member_data = resp.json()
            return member_data
        except requests.exceptions.RequestException as e:
            print(f'Error fetching member data (Attempt {attempt + 1}): {e}')
            if attempt < max_retries - 1:
                print(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
            else:
                print('Max retries exceeded. Giving up.')
                return None
        except ValueError as e:
            print(f'Error parsing JSON response: {e}')
            return None
    return None

def get_formatted_mode(data_list: list[int]):
    """Function that accepts a list, finds the mode of the values in the list
    and then formats it as currency
    """
    if not data_list:
        return None

    mode = statistics.mode(data_list)
    return f'${mode / 100:,.2f}'
