import os
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from utils.exporter import convert_to_json, remove_old_data, save_to_sqlite
from utils.parser import parsing_product, parsing_available_categories, parsing_products_on_page
from utils.utils import check_reports_folder_exist, get_requests, print_template, random_sleep


os.environ['PROJECT_ROOT'] = os.path.dirname(os.path.abspath(__file__))
futures = []


def start():
    DOMAIN = 'https://transsibmetall.ru'

    reports_folder = check_reports_folder_exist()
    if not reports_folder:
        return False

    remove_old_data(reports_folder)

    print_template("Parsing available categories...")
    categories = parsing_available_categories(f'{DOMAIN}')

    if not categories:
        print_template('Error parsing available categories!')
        return False

    for index, category in enumerate(categories):
        random_sleep(1)
        print_template(f'Start of parsing category ({index + 1}/{len(categories)}) {category}...')

        response = get_requests(category)
        if not response:
            print_template(f'Error when parsing products from category: {category}!')
            return False

        soup = BeautifulSoup(response.content, 'html.parser')

        product_links = parsing_products_on_page(DOMAIN, soup)
        if not product_links:
            continue

        navigation_pages = soup.find('div', 'navigation-pages')
        if navigation_pages:
            pages = navigation_pages.find_all('a')

            second_page = int(pages[0].get_text(strip=True))
            last_page = int(pages[-1].get_text(strip=True))

            for page in range(second_page, last_page + 1):
                print_template(f'Start of parsing category ({index + 1}/{len(categories)}) {category} page {page}...')
                url = f'{category}?PAGEN_1={page}'
                response = get_requests(url)

                if not response:
                    print_template(f'Error when parsing products from category (page {page}): {category}!')
                    return False

                soup = BeautifulSoup(response.content, 'html.parser')

                product_link_page = parsing_products_on_page(DOMAIN, soup)
                if product_link_page:
                    product_links += product_link_page

        print_template(f'Start of parsing products({len(product_links)})...')

        products_to_save = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = []
            for product_link in product_links:
                future = executor.submit(parsing_product, product_link)
                results.append(future)

            for future in results:
                result = future.result()
                if result:
                    products_to_save.append(result)
                else:
                    print_template(f'Error when parsing products!')

        print_template(f"Save products to sqlite: {len(products_to_save)} ({category})")
        save_to_sqlite(products_to_save, reports_folder)

    total_count = convert_to_json(reports_folder)
    print(f"Total count: {total_count}")


if __name__ == '__main__':
    start()
