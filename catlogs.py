import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import json
import re
import os
import pandas as pd

def get_content(url):
    user_agent = UserAgent().random.strip()
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
    else:
        return -1
    
def delete_param(url):
        match = re.match(r'([^?]*)\?', url)
        if match:
            return match.group(1)
        else:
            return url

def get_categories():
    soup = get_content("https://kaminvdom.ru/")
    data = []
    links = soup.find_all(class_='nsmenu-parent-title')
    for link in links:
        data.append(link.attrs['href'])
    with open("categories.json", 'w') as json_file:
        json.dump(data, json_file)

def get_cards(url):
    soup = get_content(f"{url}?limit=1000")
    data = []
    cards = soup.find_all(class_='product-list')
    for card in cards:
        link = card.find(class_='caption').find('a').attrs['href']
        link = delete_param(link)
        data.append(link)
    category = url.replace("https://kaminvdom.ru/", "")
    with open(f"cards/{category}.json", 'w') as json_file:
        json.dump(data, json_file)

def get_params(url):
    soup = get_content(url)
    
    name = soup.find('h1').text

    categories_res = ""
    categories = soup.find(class_="breadcrumb").find_all("span")
    for categ in categories:
        if categ.text == "":
            continue
        if name in categ.text:
            continue
        if categories_res != "":
            categories_res += "/"
        categories_res += categ.text
    
    
    images_res = []
    images = soup.find(class_='thumbnails').find_all('img')
    for image in images:
        image = image.attrs['src']
        image = image.replace('cache/', '')
        image = image[:image.rfind('-')] + image[image.rfind('.'):]
        images_res.append(image)
    images_res = ', '.join(images_res)

    ul = soup.find(class_="deshevle").find_next_sibling(class_="list-unstyled")
    brend = ul.find('img')
    if brend != None:
        brend = brend.attrs['title']
    else:
        brend = ""
    lists = ul.find_all('li')
    for li in lists:
        if 'Модель' in li.text: 
            model = li.text.replace("Модель: ", "")

    prices = soup.find_all(class_='priceprod')
    if len(prices) > 1:
        old_price = prices[0].text.replace(" руб", "")
        new_price = prices[1].text.replace(" руб", "")
    else:
        old_price = ""
        new_price = prices[0].text.replace(" руб", "")

    description = soup.find(id='tab-description').decode_contents()

    input_elements = soup.find(id='product').select("input[type='radio']")
    values = [input_element.next.strip() for input_element in input_elements]

    count = soup.find(id='product').find('input', {'name': 'quantity'}).attrs['value']

    rows = soup.find(id='tab-specification')
    spec_dict = {}
    if rows != None:
        rows = rows.select("tbody tr")
    else:
        rows = []
    for row in rows:
        col = row.find_all("td")
        name_spec = col[0].text
        value_spec = col[1].text
        spec_dict[name_spec] = value_spec

    if os.path.exists('result1.csv'):
        df = pd.read_csv('result1.csv', encoding='utf-8', sep=';')
    else:
        df = pd.DataFrame()
    
    if len(values) == 0:
        new_row = {
            'Категория' : categories_res,
            'Товар' : name,
            'Цена' : new_price,
            'Адрес' : '',
            'Видим' : count,
            'Хит' : '',
            'Бренд' : brend,
            'Вариант' : '',
            'Старая цена' : old_price,
            'Артикул' : '',
            'Склад' : '',
            'Модель' : model,
            'Заголовок страницы' : '',
            'Ключевые слова' : '',
            'Описание страницы' : '',
            'Аннотация' : '',
            'Описание' : description,
            'Изображения' : images_res
        }
        new_row.update(spec_dict)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        for value in values:
            new_row = {
                'Категория' : categories_res,
                'Товар' : name,
                'Цена' : new_price,
                'Адрес' : '',
                'Видим' : count,
                'Хит' : '',
                'Бренд' : brend,
                'Вариант' : value,
                'Старая цена' : old_price,
                'Артикул' : '',
                'Склад' : '',
                'Модель' : model,
                'Заголовок страницы' : '',
                'Ключевые слова' : '',
                'Описание страницы' : '',
                'Аннотация' : '',
                'Описание' : description,
                'Изображения' : images_res
            }
            new_row.update(spec_dict)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv('result1.csv', index=False, encoding='utf-8', sep=';')

def parse_all():
    file_names = os.listdir('cards')
    errors = {}
    for file_name in file_names:
        print(f"Парсим {file_name}")
        with open(f'cards/{file_name}', 'r') as json_file:
            urls = json.load(json_file)
            for url in urls:
                try:
                    get_params(url)
                except Exception as e:
                    print(url)
                    print(str(e))
                    errors[url] = str(e)
    with open(f"errors.json", 'w') as json_file:
        json.dump(errors, json_file)
             
def main():
    #get_categories()
    #with open("categories.json", 'r') as json_file:
    #    categories = json.load(json_file)
    #for categ in categories:
    #    get_cards(categ)
    parse_all()
    
if __name__ == "__main__":
    main()