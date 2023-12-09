#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template
from flask import request, redirect, flash
from flask import url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import click
import sys
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import make_transient
from request_gpt import generate_movie_box_office_analysis

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'mysql+mysqlconnector://root:20011106zdT@localhost/movieDB'
else:
    prefix = 'mysql+mysqlconnector://root:20011106zdT@localhost/movieDB'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = prefix
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 关闭对模型修改的监控
# 在扩展类实例化前加载配置

db = SQLAlchemy(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

login_manager.login_view = 'login'
#login_manager.login_message = 'Your custom message'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    __tablename__ = 'movie_info'

    movie_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    movie_name = db.Column(db.String(20))
    release_date = db.Column(db.DateTime)
    country = db.Column(db.String(20))
    type = db.Column(db.String(10))
    year = db.Column(db.Integer)

class MovieBox(db.Model):
    __tablename__ = 'movie_box'

    movie_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    box = db.Column(db.Float)
    review = db.Column(db.String(2048))

class ActorInfo(db.Model):
    __tablename__ = 'actor_info'

    actor_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    actor_name = db.Column(db.String(20))
    gender = db.Column(db.String(2))
    country = db.Column(db.String(20))

class MovieActorRelation(db.Model):
    __tablename__ = 'movie_actor_relation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie_info.movie_id', onupdate='CASCADE', ondelete='CASCADE'))
    actor_id = db.Column(db.Integer, db.ForeignKey('actor_info.actor_id', onupdate='CASCADE', ondelete='CASCADE'))
    relation_type = db.Column(db.String(20))

    movie = db.relationship('Movie', backref='movie_actors')
    actor = db.relationship('ActorInfo', backref='actor_movies')




@app.context_processor
def inject_user():
    return {'user': current_user}


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()

    # 获取当前应用的数据库会话
    db_session = scoped_session(sessionmaker(bind=db.engine))

    # 通过上下文管理器创建会话
    with db_session() as session:
        # 查询本地数据库的数据
        local_movies = session.query(Movie).all()
        local_actors = session.query(ActorInfo).all()
        local_movies_actors = session.query(MovieActorRelation).all()
        local_movies_boxs = session.query(MovieBox).all()
        local_users = session.query(User).all()

        # 添加到Flask应用的数据库中
        for local_movie in local_movies:
            make_transient(local_movie)  # 分离对象
            db.session.add(local_movie)

        for local_user in local_users:
            make_transient(local_user)  # 分离对象
            db.session.add(local_user)

        for local_actor in local_actors:
            make_transient(local_actor)  # 分离对象
            db.session.add(local_actor)

        for local_movies_actor in local_movies_actors:
            make_transient(local_movies_actor)  # 分离对象
            db.session.add(local_movies_actor)

        for local_movies_box in local_movies_boxs:
            make_transient(local_movies_box)  # 分离对象
            db.session.add(local_movies_box)

        db.session.commit()

    click.echo('Initialized database.')



@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')

@app.errorhandler(404)  # 传入要处理的错误代码
def page_not_found(e):  # 接受异常对象作为参数
    return render_template('404.html'), 404
    # 返回模板和状态码


@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':  # 判断是否是 POST 请求
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 重定向到主页
        # 获取表单数据
        title = request.form.get('movie_name')
        # 传入表单对应输入字段的name值
        year = request.form.get('year')
        country = request.form.get('country')
        type = request.form.get('type')
        release_date = request.form.get('yy-mm-dd')
        box = request.form.get('box')
        review = generate_movie_box_office_analysis(title)

        # 验证数据
        if not title or not year or len(title) > 60:
            flash('Invalid input.')  # 显示错误提示
            return redirect(url_for('index'))  # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(movie_name=title, year=year, release_date=release_date, country = country, type=type)  # 创建记录
        moviebox = MovieBox(box = box,review = review)
        db.session.add(movie)  # 添加到数据库会话
        db.session.add(moviebox)
        db.session.commit()  # 提交数据库会话
        flash('Item created.')  # 显示成功创建的提示
        return redirect(url_for('index'))  # 重定向回主页
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/movie/view_movie/<int:movie_id>')
def view_movie(movie_id):
    # 根据电影 ID 获取电影信息（例如，从数据库中检索该电影的详细信息）
    movie = Movie.query.get(movie_id)
    # 假设 BoxOffice 表与 Movie 表使用外键关联，并且票房信息存储在该表中
    box_office_info = MovieBox.query.filter_by(movie_id=movie_id).first()
    #print(box_office_info)

    # 假设 Cast 表与 Movie 表使用外键关联，并且主演信息存储在该表中
    cast_info = MovieActorRelation.query.filter_by(movie_id=movie_id, relation_type="主演").all()
    director_obj = MovieActorRelation.query.filter_by(movie_id=movie_id, relation_type="导演").first()
    if director_obj:
        director_id = director_obj.actor_id
        director = ActorInfo.query.filter_by(actor_id=director_id).first()
    else:
        director = ActorInfo()
        director.actor_name = "无"
    actor_ids = [cast.actor_id for cast in cast_info]
    actors = [ActorInfo.query.filter_by(actor_id=actor_id).first() for actor_id in actor_ids]
    review = MovieBox.query.filter_by(movie_id=movie_id).first()
    if not actors:
        actors = [ActorInfo()]
        actors[0].actor_name = "无"
    if movie:
        # 这里你可以执行任何操作，例如渲染一个新的页面，显示电影详情等
        return render_template('movie_details.html', movie=movie, box_office_info=box_office_info, actors=actors,
                               director=director)
    else:
        # 如果未找到电影，重定向到其他页面或者显示错误信息
        flash('Can not find movie.')
        return redirect(url_for('index'))  # 或者显示错误页面

# 编辑电影信息
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form.get('movie_name')
        year = request.form.get('year')
        if not title:
            print("not title")
        if not year:
            print("not year")
        if len(title) > 60:
            print("bad length")
        if (not title) or (not year) or (len(title) > 60):
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.movie_name = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录

@app.route('/movie/delete/<int:movie_id>', methods = ['POST'])  # 限定只接受POST请求
@login_required  # 登录保护
def delete(movie_id):
    movie = Movie.query.get(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()  # 查询用户名匹配的用户
        if user and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')

# 用户登出视图
@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        username = request.form.get('name')
        if not username or len(username) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.username = username  # 更新当前登录用户的名称
        db.session.commit()
        flash('Settings updated.')

        # 获取更新后的用户名并传递到模板中
        updated_name = current_user.name

        return render_template('settings.html', updated_name=updated_name)

    # 如果是 GET 请求，显示原始表单
    return render_template('settings.html')


@app.route('/user/<name>')
def user_page(name):
    return 'User: %s' % name


@app.route('/test')
def test_url_for():
    # 下面是一些调用示例（请在命令行窗口查看输出的 URL）：
    print(url_for('hello'))  # 输出：/
    # 注意下面两个调用是如何生成包含 URL 变量的 URL 的
    print(url_for('user_page', name='MartinZhong'))  # 输出：/user/MartinZhong
    print(url_for('user_page', name='Tim'))  # 输出：/user/Tim
    print(url_for('test_url_for'))  # 输出：/test
    # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2
    return 'Test page'
