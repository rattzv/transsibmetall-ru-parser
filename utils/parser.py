import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from utils.utils import get_current_time, get_requests, print_template, random_sleep


def parsing_products_on_page(DOMAIN, soup):
    if not soup.find('div', 'product-item-container'):
        print_template('There are no products available for parsing on our page, skip.')
        return False

    product_links = []

    product_items = soup.find_all('div', 'product-item-container')
    for product_item in product_items:
        product_links.append(f'{DOMAIN}{product_item.find("a")["href"]}')
    return list(set(product_links))


def parsing_available_categories(DOMAIN):
    response = get_requests(f'{DOMAIN}/catalog/')
    if not response:
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    catalog_body = soup.find('div', 'catalog__body__row')

    if not catalog_body:
        return False

    category_links = []

    catalog_body_links = catalog_body.find_all('a', 'catalog__body__col')
    if catalog_body_links:
        for link in catalog_body_links:
            category_links.append(f'{DOMAIN}{link["href"]}')

    return category_links if len(category_links) > 0 else False


def parsing_product(url):
    try:
        random_sleep(0.5)
        response = get_requests(url)
        if not response:
            print_template(f"Error getting product page, skip: {url}")
            random_sleep(1)
            return False

        soup = BeautifulSoup(response.content, 'html.parser')
        product = {}

        product_wrapper = soup.find('div', 'bx-catalog-element bx-yellow')
        page = soup.find('div', 'page')

        if not product_wrapper or not page:
            print_template(f"Error when parsing the product page, the key element 'bx-catalog-element bx-yellow/page' is missing, skip. ({url})")
            random_sleep(1)
            return False

        row = product_wrapper.find('div', 'row')

        product['Наименование'] = row.find('h2').get_text(strip=True).replace('"', "'").replace('\xa0', ' ')
        product['URL товара'] = url
        product['Время парсинга (мск)'] = get_current_time()
        product['Телефон города'] = \
        soup.find('div', 'header__top__row__top__tel__box').find('a', 'header__top__tel__two')[
            'href'][4:]

        price = row.find("meta", itemprop="price")["content"].replace('\xa0', '')
        product['Цена'] = price
        product['Eдиница измерения'] = row.find('div', 'productCart__price').find('span').get_text(strip=True).replace('\xa0', '').replace(
            price, '').strip()


        for p_tag in row.find('div', class_='col-md-7 col-xs-12', itemprop='offers').find_all('p'):
            split = p_tag.get_text(strip=True).split(':')
            if len(split) > 1:
                key, value = map(str.strip, split)
                product[key] = value

        breadcrumbs = soup.find('div', class_='breadcrumbs')
        if breadcrumbs:
            breadcrumbs_items = breadcrumbs.find_all('div', 'breadcrumbs_item')
            if len(breadcrumbs_items) > 2:
                chapter = breadcrumbs_items[2].get_text(strip=True)
                product['Раздел'] = chapter

        table = soup.find('div', id='content-3').find('table', 'table').text
        data_list = table.split('\n')[2:-3]
        data_list = [item for item in data_list if item != '']

        header = data_list[:6]
        rows = [data_list[i:i + 6] for i in range(6, len(data_list), 6)]

        result = {}
        for row in rows:
            city = row[0]
            city_data = dict(zip(header[1:], row[1:]))
            result[city] = city_data

        product['Доставка и оплата'] = result
        return product
    except Exception as ex:
        return False


def parsing_sitemaps(DOMAIN):
    url = f'{DOMAIN}/sitemap.xml'

    response = get_requests(url)

    if not response:
        return False

    tree = ET.ElementTree(ET.fromstring(response.content))
    root = tree.getroot()
    other_sitemap_links = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")

    sitemap_files = []
    catalog_links = []

    for sitemap_link in other_sitemap_links:
        sitemap_files.append(sitemap_link.text)

    for sitemap in sitemap_files:
        response = get_requests(sitemap)
        if not response:
            return False

        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()
        locs = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        for loc in locs:
            if "https://medexe.ru/production" in loc.text:
                catalog_links.append(loc.text)

    if len(catalog_links) > 0:
        catalog_links = list(set(catalog_links))
    return catalog_links
