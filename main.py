from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import math
from companies_list import companies
import pandas as pd
import random


STARTING_PAGE = 1
people = []


def get_driver():
    options = Options()
    options.add_argument("user-data-dir=C:\\Users\\Plavu\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    return driver


def get_linkedin_url(company, driver):
    url = f'https://www.google.com/search?q={company}+linkedin'
    driver.get(url)
    src = driver.page_source
    soup = BeautifulSoup(src, 'html.parser')
    try:
        linkedin_url = soup.find('div', class_='yuRUbf').find('a').get('href')
        return linkedin_url
    except AttributeError:
        return None
    

def check_and_transform(linkedin_url):
    separator = "."
    replacement = 'https://www'
    if replacement not in linkedin_url:
        url = linkedin_url.split('.')
        url[0] = replacement
        linkedin_url = separator.join(url)
        print(linkedin_url)
        return linkedin_url
    else:
        return linkedin_url


def transform_url(linkedin_url, driver):
    if linkedin_url:
        driver.get(linkedin_url)
        src = driver.page_source
        soup = BeautifulSoup(src, 'html.parser')
        return soup


def full_linkedin_url(soup):
    try:
        url = soup.find('div', class_='inline-block').find('a').get('href')
        full_linkedin_url = f'https://www.linkedin.com{url}'
        return full_linkedin_url
    except AttributeError:
        try:
            url = soup.find('a', class_='ember-view org-top-card-summary-info-list__info-item').get('href')
            full_linkedin_url = f'https://www.linkedin.com{url}'
            return full_linkedin_url
        except AttributeError:
            print("LinkedIn URL not found")
            return None


def get_company_name(soup):
    try:
        company_name = soup.find('span', attrs={'dir':'ltr'}).text.strip()
        return company_name
    except AttributeError: 
        try:
            company_name = soup.find('h1', class_='ember-view text-display-medium-bold org-top-card-summary__title')
            return company_name
        except AttributeError:
            print("Company Name not found")
            return None


def get_num_of_people(soup):
    try:
        init_result = soup.find('h2', class_='pb2 t-black--light t-14').text.strip().split()
        for element in init_result:
            try:
                number = int(element.replace(',', ''))
                return number
            except ValueError:
                pass    
        return 0
    except AttributeError:
        return 0


def num_of_pages(num_of_people):
    try:
        num_of_pages = math.ceil(num_of_people / 10)
        return num_of_pages
    except:
        return 0
    

def extract(transformed_url, page, driver):
    if transformed_url:
        keywords = '&keywords="Demand%20Generation"%20OR%20"Account-based%20Marketing"%20OR%20ABM%20Marketing%20OR%20"Competitive%20intelligence"%20OR%20"Competitive%20Market"'
        profile_url = f'{transformed_url}{keywords}&page={page}'
        driver.get(profile_url)
        time.sleep(3)
        src = driver.page_source
        soup = BeautifulSoup(src, 'html.parser')
        return soup


def transform(soup, company_name, page):
    if page == 1:
        try:
            ul = soup.find_all('ul', class_='reusable-search__entity-result-list list-style-none')[1]
            lis = ul.find_all('li')
        except:
            lis = ''
    elif page > 1:
        ul = soup.find_all('ul', class_='reusable-search__entity-result-list list-style-none')[0]
        lis = ul.find_all('li')
    if lis != '':
        for li in lis:
            try:
                profile_url = li.find('span', class_='entity-result__title-line').find('a', class_='app-aware-link').get('href')
            except:
                profile_url = ''
            try:
                full_name = li.find('span', class_='entity-result__title-line').find('a', class_='app-aware-link').find('span', attrs={'dir':'ltr'}).find('span', attrs={'aria-hidden':'true'}).text.strip().split()
                first_name = full_name[0]
                last_name = ' '.join(full_name[1:])
            except:
                first_name = 'Linkedin'
                last_name = 'Member'
            try:
                title = li.find('div', class_='entity-result__primary-subtitle').text.strip()
            except:
                title = ''
            person = {
                'LinkedIn Profile URL': profile_url,
                'First Name': first_name,
                'Last Name': last_name,
                'Title': title,
                'Company': company_name,
            }
            people.append(person)
    return


def time_to_sleep(people):
    if people <= 10:
        sleep_time = 15
    elif people > 10 and people <= 49:
        sleep_time = random.randint(15, 19)
    elif people > 50 and people <= 149:
        sleep_time = random.randint(20, 25)
    elif people >= 150 and people <= 300:
        sleep_time = random.randint(25, 29)
    else:
        sleep_time = random.randint(30, 34)
    return sleep_time


def scrape(driver):
    for company in companies:
        linkedin_url = get_linkedin_url(company, driver)
        checked_url = check_and_transform(linkedin_url)
        time.sleep(10)
        soup_content = transform_url(checked_url, driver)
        transformed_url = full_linkedin_url(soup_content)
        company_name = get_company_name(soup_content)
        time.sleep(10)
        content = extract(transformed_url, STARTING_PAGE, driver)
        num_of_people = get_num_of_people(content)
        pages = num_of_pages(num_of_people)
        sleep_time = time_to_sleep(num_of_people)
        print(f'Found {num_of_people} people in {company_name}, sleep time set to: {sleep_time}')
        if pages == 1:
            print(f"Getting Page 1 of {pages}", end='\r')
            transform(content, company_name, pages)
            df = pd.DataFrame(people)
            cmpny = company.replace('/', '')
            df.to_csv(f'contacts_{cmpny}.csv', index=False)
        else:
            print(f"Getting Page 1 of {pages}", end='\r')
            transform(content, company_name, STARTING_PAGE)
            for i in range(STARTING_PAGE + 1, pages + 1):
                if i <= 100:
                    time.sleep(sleep_time)
                    print(f"Getting Page {i} of {pages}", end='\r')
                    cont = extract(transformed_url, i, driver)
                    transform(cont, company_name, i)
                else:
                    df = pd.DataFrame(people)
                    df.to_csv(f'contacts_{cmpny}.csv', index=False)
                    break
        cmpny = company.replace('/', '')
        df = pd.DataFrame(people)
        df.to_csv(f'contacts_{cmpny}.csv', index=False)
        people.clear()
        time.sleep(sleep_time)
    driver.quit()


def main():
    driver = get_driver()
    scrape(driver)
    print("Scraping Done.")


if __name__ == '__main__':
    main()