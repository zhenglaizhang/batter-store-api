from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pymysql
import config
import os

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG

# 设定数据库链接
database_url = os.environ.get(
    'DATABASE_URL',
    f'mysql://{config.username}:{config.password}@{config.db_address}/{config.database_name}'
)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 配置CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 创建上传目录
os.makedirs('uploads/photos', exist_ok=True)
os.makedirs('uploads/business_licenses', exist_ok=True)

# 加载配置
app.config.from_object('config')

# 加载控制器
from wxcloudrun import views
