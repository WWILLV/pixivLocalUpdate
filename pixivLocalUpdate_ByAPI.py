# -*- coding: UTF-8 -*-
__author__ = 'WILL_V'

import os
import re
import sys
import urllib.request
import json
import getopt
import threading
from sys import exc_info
from glob import glob
from time import time, sleep
from codecs import open as codeopen
from sys import argv
from subprocess import call
from retrying import retry
from pixivpy3 import *
from math import ceil
from random import random, randint

IDM = r'' # IDMan.exe路径

# 以下为pixiv相关数据
atoken = ''
access_path = "act.txt"
refresh_token = ''
username = ''
password = ''

def getatoken():
    with open(access_path,'r') as f:
        a = f.readlines()
        if a == []:
            print("无access_token")
            exit()
        atoken = a[0]
        print("使用token:" + atoken)
        return atoken

# pixivpy3 直接连接
def direct(username, password, atoken, rtoken, _REQUESTS_KWARGS):
    if _REQUESTS_KWARGS is None:
        papi = AppPixivAPI()
    else:
        papi = AppPixivAPI(**_REQUESTS_KWARGS)
    # papi.login(username, password)
    papi.set_auth(access_token=atoken, refresh_token=rtoken)
    return papi


# 初始化pixivpy3 api
def api_init():
    access_token = getatoken()
    _REQUESTS_KWARGS = {
        'proxies': {
            'https': 'http://127.0.0.1:7890',
        },
        'verify': False,  # PAPI use https, an easy way is disable requests SSL verify
    }
    papi = direct(username=username, password=password, atoken=access_token, rtoken=refresh_token,
                  _REQUESTS_KWARGS=None)
    return papi


api = api_init()


# Python 多线程Dispatcher
class Dispacher(threading.Thread):
    def __init__(self, fun, args):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.result = None
        self.error = None
        self.fun = fun
        self.args = args

        self.start()

    def run(self):
        try:
            self.result = self.fun(self.args)
        except:
            self.error = sys.exc_info()


def checkUpdate(id, path):  # 检查是否需要更新
    for first in getPics(id, 1, '0'):
        if int(getLast(path)) < first:
            return True


def download(pics, path, last):  # 下载文件
    for pic in pics:
        if not (pic > int(last)):
            continue
        urls = pics[pic]
        try:
            for url in urls:
                filename = url[url.rfind('/') + 1:]
                imgpath = path + "\\" + filename
                if os.path.exists(imgpath):
                    continue

                print("\t[-]调用IDM下载%s，添加到队列中" % filename)
                call([IDM, '/d', url, '/p', path, '/f', filename, '/n', '/a'])
        except:
            print("\t[!]Unexpected error:", exc_info()[0])
            print("\t\033[1;31;43m[!]%d下载失败\033[0m" % pic)
            continue


def getALL(id, last):  # 获取id的所有作品
    return getPics(id, 90, last)


@retry(stop_max_attempt_number=8, wait_random_min=3, wait_random_max=10)
def getPics(id, num, last):  # 获取id的最新的num份作品
    pages = ceil(num / 30)
    illusts = api.user_illusts(id)
    dist = {}
    for page in range(pages):
        for pic in illusts['illusts']:
            if pic['id'] <= int(last):
                return dist
            picurl = []
            if len(pic['meta_single_page']) == 0:
                for p in pic['meta_pages']:
                    picurl.append(p['image_urls']['original'])
            else:
                picurl.append(pic['meta_single_page']['original_image_url'])
            dist[pic['id']] = picurl
        next_qs = api.parse_qs(illusts.next_url)
        if next_qs is None:
            return dist
        illusts = api.user_illusts(**next_qs)

    return dist


def getLast(path, update=False):  # 获取本地最新的图片id
    jsonpath = path + "\\update.json"
    if (not os.path.exists(jsonpath)) or update:
        L = []
        for root, dirs, files in os.walk(path):
            if dirs == []:  # 只走一层
                # break
                pass
            for file in files:
                if os.path.splitext(file)[1] == '.json' or os.path.splitext(file)[1] == '.url' or \
                        os.path.splitext(file)[1] == '.db':
                    continue
                # L.append(os.path.join(root, file))
                L.append(int(file[:file.find('_')]))
        last = max(L)
        return str(last)
    else:
        f = open(jsonpath, "r")
        for line in f:
            decodes = json.loads(line)
            last = decodes['last']
            return last


def urlfile(path, ext):
    for i in glob(os.path.join(path, ext)):
        yield i


def geturl(path):  # 获取url
    for i in urlfile(path, "*.url"):
        file_object = open(i)
        try:
            all_the_text = file_object.read()
            regex = r'(https://www.pixiv.net/member_illust.php\?id=\d{0,10})|' \
                    r'(https://www.pixiv.net/member.php\?id=\d{0,10})|' \
                    r'(https://www.pixiv.net/users/\d{0,10})'
            searchObj = re.search(regex, all_the_text, re.M | re.I)
            url = searchObj.group(0)
            return url
        except:
            return "ERROR"
        finally:
            file_object.close()
    return "ERROR"


def getid(path):  # 获取id
    jsonpath = path + "\\update.json"
    id = ''
    if not os.path.exists(jsonpath):
        url = geturl(path)
        if url == 'ERROR':
            return ""
        id = url.replace('https://www.pixiv.net/member_illust.php?id=', '')
        id = id.replace('https://www.pixiv.net/member.php?id=', '')
        id = id.replace('https://www.pixiv.net/users/', '')
        last = getLast(path)
        update = {}
        update['id'] = id
        update['last'] = last
        with open(jsonpath, 'w') as outfile:
            json.dump(update, outfile, ensure_ascii=False)
    else:
        f = open(jsonpath, "r")
        for line in f:
            decodes = json.loads(line)
            id = decodes['id']
    return id


def update(arg):
    id = arg["id"]
    path = arg["path"]
    last = arg["last"]
    jsonpath = arg["jsonpath"]
    finished = arg["finished"]
    if checkUpdate(id, path):
        print('[-]发现更新，爬取图片')
        all = getALL(id, last)
        download(all, path, last)
        print('\t[-]添加完成')
        print('\t[-]更新配置文件中')
        update = {}
        update['id'] = id
        update['last'] = getLast(path, True)
        with open(jsonpath, 'w') as outfile:
            json.dump(update, outfile, ensure_ascii=False)

    with codeopen(finished, 'a', 'UTF-8') as f:
        f.write(path + '\n')


@retry(stop_max_attempt_number=8, wait_random_min=25, wait_random_max=45)
def main(paths, finished, error):
    paths = checkList(paths, finished, noupdate)

    updated = []
    bancount = 0
    upcount = 1
    updateflag = False
    for path in paths:
        bancount += 1
        jsonpath = path + "\\update.json"
        # print(path)
        id = getid(path)
        if id == "":
            print('[x]' + path + '不可更新')
            with codeopen(error, 'a', 'UTF-8') as f:
                f.write(path + '\n')
            continue
        last = getLast(path)
        print('[+]更新%s的图片，id=%s   [%s/%s   %.2f%%]' % (path, id, str(upcount), str(len(paths)), (upcount/len(paths))*100))
        starttime = time()

        arg = {}
        arg["id"] = id
        arg["path"] = path
        arg["last"] = last
        arg["jsonpath"] = jsonpath
        arg["finished"] = finished

        u = Dispacher(fun=update, args=arg)
        u.join(45)
        if u.is_alive():
            print("[!]超时重试！")
            raise TimeoutError

        upcount = upcount + 1
        endtime = time()
        updated.append(path)

        print('[-]完成(%ss)' % str(int(endtime - starttime)))

        sleep(5)
    return updated


def checkList(paths, finished, noupdate):  # 使更新脚本支持中断后从断点处继续检查更新
    newpath = paths[:]
    removeList = []
    if (os.path.exists(noupdate)):
        with codeopen(noupdate, 'r', 'UTF-8') as f:  # 不更新
            for line in f:
                removeList.append(line.rstrip())
    if (not os.path.exists(finished)) or os.path.getsize(finished) == 0:
        with codeopen(finished, 'w', 'UTF-8') as f:
            f.write('')
    else:
        with codeopen(finished, 'r', 'UTF-8') as f:  # 需要重新打开文本进行读取
            for line in f:
                removeList.append(line.rstrip())
    for r in set(removeList):
        if r in newpath:
            newpath.remove(r)
    return newpath


if __name__ == '__main__':
    opts, args = getopt.getopt(argv[1:], "hf:")  # f指定目录更新
    selectPath = ''
    home = 'E:\pic\pixiv'
    starttime = time()

    L = []
    L1 = []
    print('本脚本需要使用IDM下载。')
    print('IDM地址为：%s' % IDM)
    print('正在获取文件列表...')
    for opt, arg in opts:
        if opt == '-f':
            selectPath = arg
    if (selectPath == ''):
        for root, dirs, files in os.walk(home):
            for file in files:
                L.append(root)
        [L1.append(i) for i in L if not i in L1]
        del L1[0]
    else:
        L1.append(selectPath)

    finished = 'finished.txt'
    error = 'error.txt'
    noupdate = 'NOUPDATE.txt'
    main(L1, finished, error)

    endtime = time()
    os.remove(finished)
    print('--更新完毕！--')
    print('更新共计用时' + str(int(endtime - starttime)) + 's')
    print("启动IDM队列下载")
    call([IDM, '/s'])
