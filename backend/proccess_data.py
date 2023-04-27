import logging
from module import read_reserve_data, get_cookies, initialize_data_base
from fetch_data import fetch_data
import requests

logging.basicConfig(filename='backend.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')


def make_reservation(username, day_data, meal_time: int):
    BASE_URL = 'https://self.shahroodut.ac.ir/api/v0/'
    COOKIES = get_cookies(username)
    meal_data = day_data['Meals'][meal_time]
    if day_data['Meals'][meal_time]['LastReserved'] == []:
        payload_reservation = [
            {"Row": 6, "Id": meal_data['Id'], "Date": meal_data['Date'], "MealId": meal_data['MealId'],
             "FoodId": meal_data['FoodMenu'][0]['FoodId'], "FoodName": meal_data['FoodMenu'][0]['FoodName'],
             "SelfId": 5,
             "LastCounts": 0, "Counts": 1, "Price": meal_data['FoodMenu'][0]['SelfMenu'][0]['Price'], "SobsidPrice": 0,
             "PriceType": 2, "State": 0, "Type": 1, "OP": 1,
             "OpCategory": 1, "Provider": 1, "Saved": 0, "MealName": meal_data['MealName'],
             "DayName": meal_data['DayName'],
             "SelfName": "برکت(پردیس)",
             "DayIndex": day_data['DayId'], "MealIndex": 1}]
        reserve = requests.post(url=BASE_URL + 'Reservation', cookies=COOKIES,
                                json=payload_reservation,
                                allow_redirects=False)
        logging.debug(f"Reservation request sent with status code: {reserve.status_code}")
    else:
        logging.info(f" '{meal_data['FoodMenu'][0]['FoodName']}' is already reserved for '{meal_data['DayName']}'")


def main(username):
    initialize_data_base()
    respond = fetch_data(username)
    if respond:
        reservation_data = read_reserve_data(username)
        for data in reservation_data:
            if data["DayStateTitle"] == "برنامه زمانبندی رزرو تعریف نشده است." or data['Meals'][0][
                "MealStateTitle"] == "خارج از محدوده برنامه زمانبندی رزرو" or data['Meals'][0][
                "MealStateTitle"] == "برنامه رزرو تعریف نشده است":
                logging.info(f'Day: {data["DayTitle"]} is unavailable')
            else:
                # for breakfast
                make_reservation(username, data, 0)
                # for lunch
                make_reservation(username, data, 1)
                # for dinner
                make_reservation(username, data, 2)
