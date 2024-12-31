import requests
from bs4 import BeautifulSoup
import json
import os


from spacy.lang.ru import Russian


def No_Punc(txt):
    nlp = Russian()
    doc = nlp(txt)
    txt_new = ""
    for token in doc:
        if token.text =='\n':
            txt_new += token.text
            continue
        if not token.is_alpha and not token.like_num:
            continue
        if not token.is_punct:
            txt_new += token.text + " "
    return txt_new

def ChangeNumToRome(data):
    ones = ["","I","II","III","IV","V","VI","VII","VIII","IX"]
    tens = ["","X","XX","XXX","XL","L","LX","LXX","LXXX","XC"]
    hunds = ["","C","CC","CCC","CD","D","DC","DCC","DCCC","CM"]
    thous = ["","M","MM","MMM","MMMM"]
    
    t = thous[data // 1000]
    h = hunds[data // 100 % 10]
    te = tens[data // 10 % 10]
    o =  ones[data % 10]
    
    return t+h+te+o



def ChangeArgToUrl(arg):
    arg_to_url = ""
    sym_not_change = ['*', '<', '>', '~', '"', '-', '_']
    for i in range(len(arg)):
        if 91 > ord(arg[i].encode('windows-1251')) > 64 or 123 > ord(arg[i].encode('windows-1251')) > 96 or arg[i] in sym_not_change:
            arg_to_url += arg[i]
        elif arg[i] == " ":
            arg_to_url += "+"
        else:
            arg_to_url += "%" + hex(ord(arg[i].encode('windows-1251')))[2:].upper()
    return arg_to_url


def SearchProduct(arg):
    arg_to_url = ChangeArgToUrl(arg)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 YaBrowser/24.10.0.0 Safari/537.36"
    }
    url = 'https://ilibrary.ru/search.phtml?q=' #неполная ссылка на поиск
    r = requests.get(url + arg_to_url, headers=headers) # получил html страницу
    src = r.text
    soup = BeautifulSoup(src, "lxml")
    #print(soup)
    try:
        all_variants = soup.find("ul", class_="sr").find_all("li")
    except:
        all_variants = []
    AllSearch = {}
    for var in all_variants:
        AllSearch[var.text.strip()] = "https://ilibrary.ru" + var.find("a").get("href")
    return AllSearch


def ParsingProductText(ReqData):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }
    nameProduct = ReqData[0]
    url = ReqData[1]
    num= ReqData[2]
    RnameProduct = 'AllBooks/R ' + nameProduct[:min(25, len(nameProduct))] + '.json'
    try:
        with open(RnameProduct, 'r') as file:
            dataProduct = json.load(file)
            if ('chapterName' + str(num)) in dataProduct:
                return RnameProduct
    except Exception:
        os.makedirs('AllBooks', exist_ok=True)
        with open(RnameProduct, 'w', encoding='utf-8') as file:
            json.dump({'title': nameProduct}, file)
    finally:
        r = requests.get(url, headers=headers)
        src = r.text
        soup = BeautifulSoup(src, "lxml")
        try:
            count_all_pages = int(soup.find("div", class_="bnvin").find_all('span')[1].text.strip().split('/')[1])
        except Exception:
            count_all_pages = -1
        with open(RnameProduct, 'r', encoding='utf-8') as file:
            tmp = json.load(file)
            tmp['count_all_pages'] = count_all_pages
        with open(RnameProduct, 'w', encoding='utf-8') as file:
            json.dump(tmp, file)
            tmp.clear()
        up1, up2, up3, up4, up5, up6, up7 = url.split('/')
        urlNow = up1+'/'+up2+'/'+up3+'/'+up4+'/'+up5+'/p.'+str(num) + '/' + up7
        r = requests.get(urlNow, headers=headers)
        src = r.text
        soup = BeautifulSoup(src, "lxml")
        with open(RnameProduct, "r", encoding="utf-8") as file:
            dataProduct = json.load(file)
        chapterName = ""
        try:
            chpnm1 = soup.find("div", id="text").find("h2").text.strip()
        except Exception:
            chpnm1 = ""
        try:
            chpnm2 = soup.find("div", id="text").find("h3").text.strip()
        except Exception:
            chpnm2 = ""
        if chpnm1 != "" and chpnm2 != "":
            chapterName = chpnm1 + "\n" + chpnm2
        else:
            chapterName = chpnm1 + chpnm2
        dataProduct['chapterName' + str(num)] = chapterName
        chapterText = ""
        try:
            abzacs = soup.find("div", id="text").find_all('z')
            for item in abzacs:
                chapterText += item.text.strip() + '\n'
        except Exception:
            pass
        chapterText = No_Punc(chapterText)
        dataProduct['chapterText' + str(num)] = chapterText
        with open(RnameProduct, "w", encoding="utf-8") as file:
            json.dump(dataProduct, file)
            dataProduct.clear()
    return RnameProduct



    
    
#print(SearchProduct('Отцы и дети'))

#print(ParsingProductText(['И. С. Тургенев. Отцы и дети', 'https://ilibrary.ru/text/96/p.1/index.html', 2]))

#parsing("отцы и дети", 20)