import logging
from module import generate_cookies, get_reserve_data, dump

MAX_RETRIES = 10

logging.basicConfig(filename='backend.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')

def fetch_data(username):
    for i in range(MAX_RETRIES):
        response = get_reserve_data(username)
        if response.status_code == 302:
            generate_cookies(username)
        elif response.text == 'لطفا یکبار از سیستم خارج و دوباره به سیستم ورود کنید(1).' and response.status_code == 400:
            pass
        else:
            try:
                with open(f'./reservation_datas/reservation_data_{username}.json', 'w+', encoding='utf-8') as f:
                    dump(response.json(), f, indent=4, ensure_ascii=False)
                logging.info('Data fetched successfully.')
                return True
            except Exception as e:
                logging.error(f'An error occurred while writing the data: {e}')
    logging.warning('Unable to fetch data after maximum retries.')
    return False
