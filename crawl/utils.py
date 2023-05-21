#!/usr/bin/env python
# coding=utf-8

"""
@author: Junming Liang
@license: Apache-2.0 license
@file: utils.py
@date: 2023/5/20 15:38
"""
import time
import re
from typing import List, NoReturn
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_fund_code_list():
    url = 'http://fund.eastmoney.com/fundguzhi.html'
    driver = webdriver.Chrome()
    driver.get(url)  # 加载网页

    fund_code_list = []

    type_xpath = ['/html/body/div[9]/div[2]/div[2]',
                  '/html/body/div[9]/div[2]/div[3]']
    max_pages = [13, 42]

    for xpath, max_page in zip(type_xpath, max_pages):
        button_element = driver.find_element(By.XPATH, xpath)
        button_element.click()

        table_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tContent"]'))
        )

        # soup = BeautifulSoup(driver.page_source, 'html.parser')
        # pages = soup.find_all('a', attrs={'class': 'page'})
        # max_page = int(pages[-1].text)
        for page in range(1, max_page + 1):
            page_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[11]/div[3]'))
            )

            page_input = driver.find_element(By.XPATH, '//*[@id="pager"]/div/input')
            page_input.clear()
            page_input.send_keys(page)
            time.sleep(2)
            page_confirm_button = driver.find_element(By.XPATH, '/html/body/div[11]/div[3]/div[1]/div/a')
            page_confirm_button.click()

            table_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="tContent"]'))
            )

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', attrs={'id': 'tContent'})
            for row in table.find_all('tr'):
                row_data = []
                for td in row.find_all('td'):
                    row_data.append(td.text.strip())
                if row_data:
                    fund_code_list.append(row_data[2])

    driver.close()  # 关闭网页

    return fund_code_list


def load_fund_code_list(save_path: str = './fund_codes.txt') -> List:
    try:
        with open(save_path, 'r', encoding='utf-8') as f:
            fund_codes = f.read().strip().split('\n')
    except Exception as e:
        print(e)
        fund_codes = get_fund_code_list()
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fund_codes))

    return fund_codes


def get_driver(user_agent: str = None):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument("--headless")
    options.add_argument(f"user-agent={user_agent}")

    web_driver = webdriver.Chrome(
        options=options,
    )
    web_driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                           {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => False}) "})

    return web_driver


def get_random_user_agent():
    ua = UserAgent()
    return ua.random


def execute_single_fund(fund_code: str = None):
    url = f"http://fundf10.eastmoney.com/jjjz_{fund_code}.html"
    driver = get_driver(user_agent=get_random_user_agent())
    try:
        file = open(f"./data/fund_net_price_{fund_code}.txt", 'w', encoding='utf-8')

        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            driver.get(url)  # 加载网页

            # 等待页面返回
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'pagebtns'))
                )
                break
            except Exception as e:
                print(f"{fund_code} page failed {retry_count + 1} times, Reason: ", e)
                driver = get_driver(user_agent=get_random_user_agent())

            # 增加重试次数
            retry_count += 1
        if retry_count == 3:
            print(f'Crawl {fund_code} failed.')
            return

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pagebtns = soup.find('div', attrs={'class': 'pagebtns'})
        max_page = pagebtns.find_all('label')[-2].text

        for page in range(1, int(max_page) + 1):
            input_element = driver.find_element(By.CLASS_NAME, 'pnum')
            input_element.send_keys(page)
            button_element = driver.find_element(By.CLASS_NAME, 'pgo')
            button_element.click()

            page_soup = BeautifulSoup(driver.page_source, 'html.parser')

            table = page_soup.find('table', attrs={'class': 'w782 comm lsjz'})
            exceed_time = 1
            start = time.time()
            end = time.time()
            while not table and end - start < exceed_time:
                time.sleep(0.1)
                page_soup = BeautifulSoup(driver.page_source, 'html.parser')
                table = page_soup.find('table', attrs={'class': 'w782 comm lsjz'})
                end = time.time()
            if not table:
                print(f'Crawl {fund_code}-{page} failed')
                return

            for row in table.find_all('tr'):
                row_data = []
                for td in row.find_all('td'):
                    row_data.append(td.text.strip())
                if row_data:
                    row_data = '\t'.join(row_data)
                    file.write(row_data + '\n')

        file.close()
    except Exception as e:
        print(f'At last crawl {fund_code} failed.', e)

    driver.close()


def execute_single_fund_position(fund_code: str = None) -> NoReturn:
    url = f'http://fundf10.eastmoney.com/ccmx_{fund_code}.html'
    driver = get_driver(user_agent=get_random_user_agent())
    try:
        file = open(f"./data/fund_stock_position_{fund_code}.txt", 'w', encoding='utf-8')

        # 等待table出现
        max_retries = 3
        retry_count = 0
        table = None
        while retry_count < max_retries:
            driver.get(url)  # 加载网页
            time.sleep(0.25)

            # 等待页面返回
            try:
                table = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.XPATH, '//table[contains(@class, "w782 comm tzxq")]'))
                )
                break
            except:
                # print(f"{fund_code} page's table not found {retry_count + 1} times")
                driver = get_driver(user_agent=get_random_user_agent())

            # 增加重试次数
            retry_count += 1
        if retry_count == 3 and not table:
            print(f'{fund_code} page has no table. ')
            return

        # 是否有年份页面选择
        year_button = None
        try:
            year_button = driver.find_element(By.XPATH, '//div[@class="pagebtns"]')
        except:
            pass

        if year_button:
            max_year = year_button.text[:4]
            max_year_button = driver.find_element(By.XPATH, f'//div[@class="pagebtns"]/label[@value={max_year}]')
            max_year_button.click()

            table = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, '//table[contains(@class, "w782 comm tzxq")]'))
            )

        # expand_button
        expand_button = driver.find_element(By.XPATH, '//a[@style="cursor:pointer;"]')

        if "显示全部持仓明细" in expand_button.text:
            expand_button.click()

            table = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, '//table[contains(@class, "w782 comm tzxq")]'))
            )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table_pattern = re.compile(r"w782\scomm\stzxq.*")
        table = soup.find('table', attrs={'class': table_pattern})
        for row in table.find_all('tr'):
            row_data = []
            for td in row.find_all('td'):
                row_data.append(td.text.strip())
            if row_data:
                row_data = '\t'.join(row_data)
                file.write(row_data + '\n')

        file.close()
    except Exception as e:
        print(f"Crawl {fund_code} failed. Reason: ", e)

    driver.close()
