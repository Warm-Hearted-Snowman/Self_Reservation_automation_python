from module import get_cookies, generate_cookies, get_reserve_data, dump

MAX_RETRIES = 10


def fetch_data():
    for i in range(MAX_RETRIES):
        response = get_reserve_data()
        if response.status_code == 302:
            generate_cookies('40019823', '1')
        else:
            with open('reservation_data.json', 'w+', encoding='utf-8') as f:
                dump(response.json(), f, indent=4, ensure_ascii=False)
            return True
    return False


def main():
    fetch_data()


if __name__ == '__main__':
    main()
