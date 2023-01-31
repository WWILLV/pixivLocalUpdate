## pixivLocalUpdate

> **本脚本不属于一键式操作脚本，仅自用开源，不保证后续更新**

自用pixiv本地图库更新，基于pixivpy3实现，使用前需自行配置pixiv相关token。

下载使用IDM，可自行配置其他下载方法。

如需代理，可使用命令：

```bash
set http_proxy=url & set https_proxy=url
```

使用前需使用pixiv_auth对access_token获取，随后便可使用pixivLocalUpdate_ByAPI进行更新。

更新文件夹要求要其目录下有指向作者pixiv主页的快捷方式（.url）或包含作者uid的update.json文件。

由于本项目从2018年开始陆续更新至今，一直自用且未考虑规范化，代码冗余严重敬请谅解。