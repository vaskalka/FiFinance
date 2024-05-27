import requests
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup as BS
import json


# Открываем файл и читаем его содержимое
with open('local.dev.json', 'r') as f:
    auth_data = json.load(f)

# Токен доступа к боту
folderid = auth_data["FOLDER_ID"]
# Токен доступа к api парсинга чеков
apikey = auth_data["API_YANDEX_KEY"]


class HTTPClient:
    def __init__(self):
        self.session = requests.Session()

    def get(self, url):
        response = self.session.get(url)
        return response


def parse_data(position, base_url):
    options = Options()
    options.headless = True  # Делает браузер невидимым, если True
    driver = webdriver.Firefox(options=options)

    driver.get(base_url)
    # Подождем несколько секунд, чтобы убедиться, что весь контент загружен
    import time
    time.sleep(7)

    # Получаем рендеренный HTML-код страницы
    rendered_html = driver.page_source

    # Преобразуем HTML в объект BeautifulSoup для парсинга
    soup = BS(rendered_html, "html.parser")

    # Найдем все элементы с классом "NutritionFacts_propertyCell__yMNSK"
    items = soup.find_all("div", {"class": "NutritionFacts_propertyCell__yMNSK"})

    unique_items = set()

    for item in items:
        property_name = item.find("div", {"class": "NutritionFacts_propertyName__HQwv2"}).text.strip()
        property_value = item.find("div", {"class": "NutritionFacts_propertyValue__AtqxR"}).text.strip()

        property_string = f'{property_name}: {property_value}'
        unique_items.add(property_string)

    for item in unique_items:
        print(f'item = {item}')

    driver.quit()


def main():
    client = HTTPClient()
    query = [
        'БЗМЖ СЫР ПЛ.VIOLA СЛИВОЧНЫЙ 45% СЛАЙСЫ 140Г',
        'ПИТАХАЙЯ 1ШТ',
        'ЯБЛОКИ ГРЕННИ СМИТ ВЕС',
        'ЛУК КРАСНЫЙ В УПАК 1ШТ'
    ]
    for position in query:
        url = (
            f'https://yandex.ru/search/xml?folderid={folderid}'
            f'&apikey={apikey}&query=sbermarket {position}'
            f'&lr=11316&l10n=ru&sortby=rlv&filter=strict'
            f'&groupby=attr%3Dd.mode%3Ddeep.groups-on-page%3D5.docs-in-group%3D3&maxpassages=3&page=0'
        )
        response = client.get(url)
        urls = list()
        if response.status_code == 200:
            data = response.text
            # pprint(f'data: {data}')

            # Теперь парсим XML
            root = ET.fromstring(data)
            # Ищем теги <doc>
            for doc in root.findall('.//doc'):
                # Ищем тег <url> внутри каждого <doc>
                url_tag = doc.find('url')
                if url_tag is not None:
                    url = url_tag.text
                    urls.append(url)
            print(f"urls: {urls}")

            if urls:
                for url in urls:
                    if 'sbermarket' in url:
                        base_url = url
                        print(f'base_url: {url}')
                        print(f'name: {position}')
                        parse_data(position, base_url)
                        break


if __name__ == '__main__':
    main()
