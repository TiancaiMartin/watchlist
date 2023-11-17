#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template

from flask import url_for

from faker import Faker
#用于自动生成假数据
from faker.providers import BaseProvider
from lorem_text import lorem
import random

movie = {}
num_entries = 15 #条目数量
# 自定义 Provider
class CustomProvider(BaseProvider):

    def custom_title(self):
        return lorem.words(3) #生成由三个单词组成的随机英文词组
    def custom_year(self):
        return random.randint(1950, 2022)  # 生成 1950 到 2022 年之间的随机年份

fake = Faker()
fake.add_provider(CustomProvider)

# 批量创建用户数据
for i in range(num_entries):
    movie[fake.name()]={
        'title': fake.custom_title,
        'year': fake.custom_year()
    }

#print(movie)
name = 'Martin Zhong'
movies = [
{'title': 'My Neighbor Totoro', 'year': '1988'},
{'title': 'Dead Poets Society', 'year': '1989'},
{'title': 'A Perfect World', 'year': '1993'},
{'title': 'Leon', 'year': '1994'},
{'title': 'Mahjong', 'year': '1996'},
{'title': 'Swallowtail Butterfly', 'year': '1996'},
{'title': 'King of Comedy', 'year': '1999'},
{'title': 'Devils on the Doorstep', 'year': '1999'},
{'title': 'WALL-E', 'year': '2008'},
{'title': 'The Pork of Music', 'year': '2012'},
]

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html', name=name, movies=movies)

@app.route('/user/<name>')
def user_page(name):
    return 'User: %s' % name

@app.route('/test')
def test_url_for():
#下面是一些调用示例（请在命令行窗口查看输出的 URL）：
    print(url_for('hello')) # 输出：/
# 注意下面两个调用是如何生成包含 URL 变量的 URL 的
    print(url_for('user_page', name='MartinZhong')) # 输出：/user/MartinZhong
    print(url_for('user_page', name='Tim')) # 输出：/user/Tim
    print(url_for('test_url_for')) # 输出：/test
# 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL后面。
    print(url_for('test_url_for', num=2)) # 输出：/test?num=2
    return 'Test page'


