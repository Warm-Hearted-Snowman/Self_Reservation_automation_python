import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR + '\\backend')
import logging
import backend_module
import proccess_data

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')


async def main(user_id, flag: bool):
    logging.info('Starting main function')
    user = backend_module.User(user_id)
    proccess_data.main(user, flag)
    logging.info('Finished main function')
    if flag:
        return backend_module.load_reserve_result(user)
    else:
        return backend_module.load_reserved_foods(user)