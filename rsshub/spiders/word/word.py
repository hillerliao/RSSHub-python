import random
import linecache
import sys
from os import path

file_path = path.dirname(path.realpath(__file__))

def ctx():
    file = path.join(file_path,'toeflwords.txt')
    with open(file, encoding='utf-8') as inf:
        f = inf.readlines()
        count = len(f)
        wordnum = random.randrange(0, count, 1)
        word = linecache.getline(file, wordnum)
        return {"word": word}
