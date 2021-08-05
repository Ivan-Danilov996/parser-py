import csv
import time
import webbrowser

import requests
from bs4 import BeautifulSoup
from pprint import pprint
import json

timeout = 10

HOST = 'http://bazarpnz.ru/'

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36",
    'accept': '*/*'
}

FILE = 'kompjutery_orgtexnika.json'

PARENT_CATEGORIES = ['dlja_detej/', 'audio_video/', 'bytovaja_texnika/', 'zdorovje_krasota/', 'kompjutery_orgtexnika/',
                     'mebel_interjer/', 'mobilnye_ustrojstva_i_aksessuary/', 'oborudovanie_stanki/',
                     '/odezhda_obuv_aksessuary/',
                     'ohota_rybalka_turizm/', 'produkty_selskoe_xozjajstvo/', 'svjaz_telekommunikatsii/',
                     'tovary_dlja_sporta_i_otdyxa/',
                     'foto_muzyka_iskusstvo/', 'zhivotnye_rastenija/']

PARENT_CATEGORIES = ['kompjutery_orgtexnika/']


def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_categories(url):
    soup = BeautifulSoup(get_html(url).text, 'html.parser')
    items = soup.find('table', id='table_rub').find_all('a')
    categories = []
    for item in items:
        categories.append({'link': item.get('href'), 'name': item.get_text(strip=True)})
    return categories


def get_pages_count(html):
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('td', class_="pages")
    if pagination:
        return pagination.find_all('a')[-2].get_text(strip=True)
    else:
        return 1


def get_content(html, category):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('tr', class_='vithot')
    products = []
    if len(items) == 0:
        print(f'товаров не найдено')
        return products

    for i, item in enumerate(items):
        time.sleep(timeout)
        print(f'обработано {i + 1} товаров из {len(items)}')
        product_view = get_html(item.find('div', 'vdatext').find('a').get('href'))
        product_soup = BeautifulSoup(product_view.text, 'html.parser')
        if product_soup.find('div', class_='boxpink'):
            print('error')
            webbrowser.open_new(item.find('div', 'vdatext').find('a').get('href'))
            click = input('click captcha')
            product_view = get_html(item.find('div', 'vdatext').find('a').get('href'))
            product_soup = BeautifulSoup(product_view.text, 'html.parser')
        if not product_soup.find('div', id="vitrina-title"):
            continue
        product_price = product_soup.find('span', class_="price")
        product_title = product_soup.find('h1')
        product_description = product_soup.find('p', class_="adv_text")
        product_shop = product_soup.find('div', id="vitrina-title").find('span')
        product_img = product_soup.find('img', id="bigfoto")
        shop_img = product_soup.find('img', id="vit_img")
        shop_address = product_soup.find('div', id='vitrina-title').find_all(text=True, recursive=False)
        shop_address = [title_item.strip() for title_item in shop_address]
        shop_address = [title_item for title_item in shop_address if title_item]
        shop_phone = ''
        for string in shop_address:
            if string.lower().count('тел.') != 0:
                to_lower_phone = string.lower()
                shop_phone = to_lower_phone.replace("тел.", "")
        shop_phone = shop_phone.replace(":", "")
        shop_data = product_soup.find('div', id='vitrina-title').findChildren('a')
        shop_mail = ''
        shop_site = ''
        if len(shop_data) > 1:
            for data in shop_data:
                if data.get_text(strip=True).count('@') != 0:
                    shop_mail = data.get_text(strip=True)
                if data.get('target') == '_blank' and data.get_text(strip=True):
                    shop_site = data.get_text(strip=True)
        product = {
            'title': product_title.get_text(strip=True) if product_title else 'Без наименования',
            'price': product_price.get_text(strip=True).replace("руб.",
                                                                "") if product_price else 'Цену оточняйте у продавца',
            'description': product_description.get_text() if product_description else 'Описание отсутствует',
            'shop': product_shop.get_text(strip=True) if product_shop else 'Наименование отсутсвует',
            'img': HOST + product_img.get('src') if product_img else 'Изображение отсутствует',
            'category': category,
            'shop_address': shop_address[0],
            'shop_img': HOST + shop_img.get('src') if shop_img else 'Изображение отсутствует',
            'shop_phone': shop_phone.strip(),
            'shop_mail': shop_mail.replace('mailto:', '') if shop_mail else 'Email отсутствует',
            'shop_site': shop_site.strip()
        }
        products.append(product)
        pprint(product)
    return products


def save_file(items, path):
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(
            ['title', 'price', 'description', 'shop', 'img', 'category', 'shop_address', 'shop_img', 'shop_phone',
             'shop_mail', 'shop_site'])
        for item in items:
            writer.writerow(
                [item['title'], item['price'], item['description'], item['shop'], item['img'], item['category'],
                 item['shop_address'], item['shop_img'], item['shop_phone'], item['shop_mail'], item['shop_site']])


def save_file_json(items, path):
    with open(path, "w") as write_file:
        json.dump(items, write_file)


def parse():
    products = []
    for parent_category in PARENT_CATEGORIES:
        url = HOST + parent_category
        print(f'Получаем все категории {parent_category}')
        time.sleep(timeout)
        categories = get_categories(url)
        for category in categories:
            print(f'Получаем все товары {category["name"]}')
            time.sleep(timeout)
            child_url = url + category['link']
            html = get_html(child_url)
            if html.status_code == 200:
                pages_len = get_pages_count(html.text)
                print(f'pages: {pages_len}, {child_url}')
                for page in range(int(pages_len)):
                    print(f'Обработка {page + 1} страницы категории {category["name"]}')
                    time.sleep(timeout)
                    html = get_html(child_url, params={'p': page * 45})
                    try:
                        product = get_content(html.text, category['name'])
                        products.extend(product)
                    except:
                        products.extend([{
                            'title': '',
                            'price': '',
                            'description': '',
                            'shop': '',
                            'img': '',
                            'category': '',
                            'shop_address': '',
                            'shop_img': ''
                        }])
                        break
            else:
                print('error')
    save_file_json(products, FILE)


print(parse())


with open("tovary_dlja_sporta_i_otdyxa.json", "r") as read_file:
    data = json.load(read_file)
    pprint(data)