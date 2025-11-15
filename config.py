import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 是否开启debug模式
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", os.environ.get("MYSQL_USERNAME", "battery_user"))
password = os.environ.get("MYSQL_PASSWORD", os.environ.get("MYSQL_PASSWORD", "password"))
db_address = os.environ.get("MYSQL_ADDRESS", os.environ.get("MYSQL_ADDRESS", "localhost:3306"))
database_name = os.environ.get("MYSQL_DATABASE", "battery_recycling")

# 服务器配置
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "80"))

# 日志级别
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")
