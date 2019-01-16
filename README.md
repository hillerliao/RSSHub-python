# RSSHub

> 🍰 万物皆可 RSS

RSSHub 是一个轻量、易于扩展的 RSS 生成器，可以给任何奇奇怪怪的内容生成 RSS 订阅源

本项目是[原RSSHub](https://github.com/DIYgod/RSSHub)的Python实现。

**其实用Python写爬虫要比JS更方便:p**

DEMO地址：https://rsshub-python.herokuapp.com

## RSS过滤

你可以通过以下查询字符串来过滤RSS的内容：

- include_title: 搜索标题
- include_description: 搜索描述
- exclude_title: 排除标题
- exclude_description: 排除描述
- limit: 限制条数

## 贡献RSS方法

1. fork这份仓库
2. 在spiders文件夹下创建新的爬虫目录和脚本，编写爬虫，参考我的[爬虫教程](https://alphardex.github.io/2018/12/15/%E7%BD%91%E7%BB%9C%E7%88%AC%E8%99%AB%E7%B2%BE%E8%A6%81/)
3. 在blueprints的main.py中添加对应的路由（按照之前路由的格式）
4. 提pr

## 部署

### 搭建

首先确保安装了[pipenv](https://github.com/pypa/pipenv)

``` bash
git clone https://github.com/alphardex/RSSHub-python
cd RSSHub-python
pipenv install --dev
pipenv shell
```

### 运行

``` bash
flask run
```

### 部署到Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/alphardex/RSSHub-python)

记得在环境变量中把FLASK_CONFIG设为production
