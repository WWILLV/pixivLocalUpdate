# -*- coding: UTF-8 -*-
__author__ = 'WILL_V'

import os
from random import choice
from PIL import Image

home = ""  # 图片目录
blackList = "blacklist.txt"  # 黑名单列表
allowfile = ['jpg', 'png']  # 允许的后缀名
minLength = 1200  # 最小长
minWidth = 900  # 最小宽
widescreen = True  # 是否为宽屏图片
selectPx = True  # 是否选择多p图片


L = []
bL = []


# 检查黑名单
if os.path.exists(blackList):
    with open(blackList, 'r') as f:
        for line in f:
            bL.append(line.rstrip())
else:
    with open(blackList, 'a') as f:
        pass


# 图片过滤
def filter(pic):
    img = Image.open(pic)
    length = img.size[0]
    width = img.size[1]
    if not selectPx:
        if (pic[pic.rfind("_p"):pic.rfind(".")]).lower() != "_p0":
            return False
    if length < minLength or width < minWidth:
        return False
    if widescreen and length > width:
        return True
    return False


# 遍历图片
for root, dirs, files in os.walk(home):
    if root in bL:
        continue
    for file in files:
        for allowed in allowfile:
            if file.endswith(allowed):
                L.append(root+'\\'+file)

print("%s 下共有%d张图片" % (home, len(L)))
while(True):
    pic = choice(L)
    if filter(pic):
        print(pic)
        os.system(pic)
        userinput = -1
        while(True):
            userinput = int(input('''
请选择操作：
1. 查看下一张图片
2. 打开该文件夹
3. 拉黑该文件夹
4. 退出
'''))
            if userinput > 0 and userinput < 5:
                break
            print("输入有误，重新输入！")

        if userinput == 1:
            continue
        if userinput == 2:
            os.system("explorer.exe %s" % os.path.dirname(pic))
        if userinput == 3:
            with open(blackList, "a+") as f:
                f.write(os.path.dirname(pic)+"\n")
        else:
            break

    continue
