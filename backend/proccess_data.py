import json
import logging
from backend_module import load_reserve_data, get_cookies, initialize_data_base, User, dump_reserve_result, \
    dump_reserved_foods, make_priority_queue
from fetch_data import fetch_data
import requests

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')

BASE_URL = 'https://self.shahroodut.ac.ir/api/v0/'


def make_reservation(user: User, day_data, meal_time: int, cookies):
    """
    Makes a reservation for a specific meal time.

    Args:
        user (User): User object containing user information.
        day_data (dict): Data for the specific day.
        meal_time (int): Meal time index (0 for breakfast, 1 for lunch, 2 for dinner).
        cookies (dict): Cookies for authentication.

    Returns:
        str: The reserved food name if successful, an error message otherwise.
    """
    # Log user-related information
    logging.info(f"User ID: {user.user_id}")
    logging.info(f"Username: {user.username}")

    meal_data = day_data['Meals'][meal_time]
    priority_queue = make_priority_queue(user)
    flag = 0
    if meal_time != 0 and priority_queue.get(meal_data['FoodMenu'][0]['FoodName'], 0) < priority_queue.get(
            meal_data['FoodMenu'][1]['FoodName'], 0):
        flag = 1
    if not meal_data['LastReserved']:
        payload_reservation = [
            {"Row": 6, "Id": meal_data['Id'], "Date": meal_data['Date'], "MealId": meal_data['MealId'],
             "FoodId": meal_data['FoodMenu'][flag]['FoodId'], "FoodName": meal_data['FoodMenu'][flag]['FoodName'],
             "SelfId": 5,
             "LastCounts": 0, "Counts": 1, "Price": meal_data['FoodMenu'][flag]['SelfMenu'][0]['Price'],
             "SobsidPrice": 0,
             "PriceType": 2, "State": 0, "Type": 1, "OP": 1,
             "OpCategory": 1, "Provider": 1, "Saved": 0, "MealName": meal_data['MealName'],
             "DayName": meal_data['DayName'],
             "SelfName": "برکت(پردیس)",
             "DayIndex": day_data['DayId'], "MealIndex": 1}]

        proxies = {
            "http": None,
            "https": None
        }
        reserve = requests.post(url=BASE_URL + 'Reservation', cookies=cookies, json=payload_reservation,
                                allow_redirects=False, proxies=proxies)
        logging.debug(f"Reservation request sent with status code: {reserve.status_code}")
        if json.loads(reserve.text)[0]['StateMessage'] == 'موجودی کافی نمی باشد':
            logging.error('موجودی کافی نمی باشد')
            return 'موجودی کافی نمی باشد'
        else:
            logging.info(f" '{meal_data['FoodMenu'][flag]['FoodName']}' reserved for '{meal_data['DayName']}'")
    else:
        logging.info(f" '{meal_data['FoodMenu'][flag]['FoodName']}' is already reserved for '{meal_data['DayName']}'")

    return meal_data['FoodMenu'][flag]['FoodName']


def main(user: User, flag: bool):
    """
    Main function for making reservations or fetching already reserved foods.

    Args:
        user (User): User object containing user information.
        flag (bool): Flag indicating whether to make reservations (True) or fetch already reserved foods (False).
    """
    logging.info(f"User ID: {user.user_id}")
    logging.info(f"Username: {user.username}")

    initialize_data_base()
    logging.info("Database initialized")

    respond = fetch_data(user)
    if respond and flag:
        reservation_data = load_reserve_data(user)  # Fixed method call to read_reserve_data
        cookies = get_cookies(user)
        result = []
        for data in reservation_data:
            day_state_title = data.get("DayStateTitle")
            meal_state_title = data['Meals'][0].get('MealStateTitle')
            meal_result = {"day": data.get("DayTitle")}  # Create a separate dictionary for each meal

            # Log day state title and meal state title of each meal
            logging.info(f"Day Title: {data.get('DayTitle')}")
            logging.info(f"Day State Title: {day_state_title}")
            logging.info(f"Meal State Title: {meal_state_title}")

            if day_state_title == "برنامه زمانبندی رزرو تعریف نشده است.":
                logging.error(f'Day: {data["DayTitle"]} : برنامه زمانبندی رزرو تعریف نشده است')
                meal_result['error'] = "برنامه زمانبندی رزرو تعریف نشده است."
            elif meal_state_title == "خارج از محدوده برنامه زمانبندی رزرو":
                logging.error(f'Day: {data["DayTitle"]}  خارج از محدوده برنامه زمانبندی رزرو')
                meal_result['error'] = "خارج از محدوده برنامه زمانبندی رزرو"
            elif meal_state_title == "برنامه رزرو تعریف نشده است":
                logging.error(f'Day: {data["DayTitle"]} برنامه رزرو تعریف نشده است ')
                meal_result['error'] = "برنامه رزرو تعریف نشده است"
            else:
                meal_result['food'] = {}
                # for breakfast
                meal_result['food']['breakfast'] = make_reservation(user, data, 0, cookies)
                # for lunch
                meal_result['food']['lunch'] = make_reservation(user, data, 1, cookies)
                # for dinner
                meal_result['food']['dinner'] = make_reservation(user, data, 2, cookies)

            result.append(meal_result)  # Append the meal's dictionary to the results list

        dump_reserve_result(user, result)  # Save the entire list of meal dictionaries
        logging.info("Reservations saved successfully")
    if not flag:
        reservation_data = load_reserve_data(user)  # Fixed method call to read_reserve_data
        result = []
        for data in reservation_data:
            day_state_title = data.get("DayStateTitle")
            meal_state_title = data['Meals'][0].get('MealStateTitle')
            meal_result = {"day": data.get("DayTitle")}  # Create a separate dictionary for each meal

            # Log day state title and meal state title of each meal
            logging.debug(f"Processing data for day: {data.get('DayTitle')}")
            logging.debug(f"Day State Title: {day_state_title}")
            logging.debug(f"Meal State Title: {meal_state_title}")

            if day_state_title == "برنامه زمانبندی رزرو تعریف نشده است.":
                logging.error(f'Day: {data["DayTitle"]} : برنامه زمانبندی رزرو تعریف نشده است')
                meal_result['error'] = "برنامه زمانبندی رزرو تعریف نشده است."
            elif meal_state_title == "برنامه رزرو تعریف نشده است":
                logging.error(f'Day: {data["DayTitle"]} برنامه رزرو تعریف نشده است ')
                meal_result['error'] = "برنامه رزرو تعریف نشده است"
            else:
                meal_result = {"day": data.get("DayTitle"), 'food': {}}  # Create a separate dictionary for each meal
                for reserved in data["Meals"]:
                    try:
                        reserved = reserved["LastReserved"][0]
                    except:
                        pass
                    if reserved.get('Id') % 3 == 1:
                        meal_result['food']['breakfast'] = reserved.get("FoodName")
                    elif reserved.get('Id') % 3 == 2:
                        meal_result['food']['lunch'] = reserved.get("FoodName")
                    elif reserved.get('Id') % 3 == 0:
                        meal_result['food']['dinner'] = reserved.get("FoodName")

                # Log the processed meal data
                logging.info(f"Processed data for day: {data.get('DayTitle')}")
                logging.debug(f"Meal Result: {meal_result}")

            result.append(meal_result)  # Append the meal's dictionary to the results list

        # Log the final results
        logging.info(f"Dumping reserved foods for user: {user}")
        logging.debug(f"Result: {result}")
        dump_reserved_foods(user, result)
