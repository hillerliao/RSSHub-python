import csv
import random 
import requests
import linecache
from os import path
import requests
from rsshub.utils import DEFAULT_HEADERS


file_path = path.dirname(path.realpath(__file__))

def get_csv_line(url):
    response = requests.get(url)
    lines = response.text.splitlines()
    reader = csv.reader(lines)
    data = list(reader)
    data = data[1:]
    random_line = random.choice(data)
    return random_line

def ctx(category=''):
    word = ''
    if category == 'ja':
        url = 'https://raw.githubusercontent.com/hillerliao/img/main/words.csv'
        res = get_csv_line(url)
        word = f"{res[1]} 〔{res[2]}〕 {res[3]} "
    else:
        file = path.join(file_path,'toeflwords.txt')
        with open(file, encoding='utf-8') as inf:
            f = inf.readlines()
            count = len(f)
            wordnum = random.randrange(0, count, 1)
            word = linecache.getline(file, wordnum)
    return {"word": word}