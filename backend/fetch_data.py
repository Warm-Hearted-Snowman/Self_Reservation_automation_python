import logging
from backend_module import generate_cookies, get_reserve_data, dump, User, dump_reserve_data

MAX_RETRIES = 10

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s',
    encoding='utf-8'
)

def fetch_data(user: User):
    """
    Fetches data for a user from the backend system.

    Args:
        user (User): The user for which the data is fetched.

    Returns:
        bool: True if data is fetched and dumped successfully, False otherwise.
    """
    for i in range(MAX_RETRIES):
        response = get_reserve_data(user)

        if response.status_code == 302:
            logging.debug('Received a redirect response. Generating new cookies...')
            generate_cookies(user)
        elif response.text == 'لطفا یکبار از سیستم خارج و دوباره به سیستم ورود کنید(1).' and response.status_code == 400:
            logging.warning('Session expired. Generating new cookies...')
            generate_cookies(user)
            return fetch_data(user)
        else:
            try:
                dump_reserve_data(user, response)
                logging.info('Data fetched and dumped successfully.')
                return True
            except Exception as e:
                logging.error(f'An error occurred while writing the data: {e}')

    logging.error('Unable to fetch data after maximum retries.')
    return False

