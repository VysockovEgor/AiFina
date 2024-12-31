import requests
from lxml import html
from bs4 import BeautifulSoup
import time
import random
import json
import os,re
import NoPunc


def ChangeArgToUrl(arg):
    arg_to_url = ""
    sym_not_change = ['*', '<', '>', '~', '"', '-', '_']
    for i in range(len(arg)):
        if 91 > ord(arg[i].encode('windows-1251')) > 64 or 123 > ord(arg[i].encode('windows-1251')) > 96 or arg[
            i] in sym_not_change:
            arg_to_url += arg[i]
        elif arg[i] == " ":
            arg_to_url += "+"
        else:
            arg_to_url += "%" + hex(ord(arg[i].encode('windows-1251')))[2:].upper()
    return arg_to_url
def get_page(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    texts = [z.get_text()+'\n' for z in soup.find_all('z')]
    combined_text = " ".join(texts)
    '''try:
        page = str(soup.find('div', id='bnav').find('span', style='display:block;text-indent:0em;padding:.6em;font-size:90%;white-space:nowrap').text).split('/')[1]
    except: page=0'''
    return combined_text
def SearchProduct(arg):
    arg_to_url = ChangeArgToUrl(arg)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }
    url = 'https://ilibrary.ru/search.phtml?q='  # неполная ссылка на поиск
    r = requests.get(url + arg_to_url, headers=headers)  # получил html страницу
    src = r.text
    soup = BeautifulSoup(src, "lxml")
    # print(soup)
    try:
        all_variants = soup.find("ul", class_="sr").find_all("li")
    except:
        all_variants = []
    AllSearch = {}
    for var in all_variants:
        AllSearch[var.text.strip()] = "https://ilibrary.ru" + var.find("a").get("href")
    return AllSearch

