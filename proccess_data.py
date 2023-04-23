from module import read_reserve_data
from fetch_data import get_cookies, generate_cookies, fetch_data, get_reserve_data
import requests

BASE_URL = 'https://self.shahroodut.ac.ir/api/v0/'
COOKIES = get_cookies()


def make_reservation(day_data, meal_time: int):
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
        print(reserve.status_code)
    else:
        print(f"{meal_data['FoodMenu'][0]['FoodName']} is reserved for {meal_data['DayName']}")


def main():
    respond = fetch_data()
    if respond:
        reservation_data = read_reserve_data()
        for data in reservation_data:
            if data["DayStateTitle"] == "برنامه زمانبندی رزرو تعریف نشده است." or data['Meals'][0][
                "MealStateTitle"] == "خارج از محدوده برنامه زمانبندی رزرو" or data['Meals'][0][
                "MealStateTitle"] == "برنامه رزرو تعریف نشده است":
                print(f'Day: {data["DayTitle"]} is unavailable')
            else:
                # for breakfast
                make_reservation(data, 0)
                # for lunch
                make_reservation(data, 1)
                # for dinner
                make_reservation(data, 2)


if __name__ == '__main__':
    main()
