#!/usr/bin/env python
# coding=utf-8

"""
@author: Junming Liang
@license: Apache-2.0 license
@file: get_historical_nev.py
@date: 2023/5/20 15:50
"""
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from utils import load_fund_code_list, execute_single_fund


if __name__ == '__main__':
    fund_codes = load_fund_code_list(save_path='./fund_codes.txt')
    with Pool(processes=cpu_count() - 2) as pool:
        result = list(tqdm(pool.imap(execute_single_fund, fund_codes), total=len(fund_codes)))
