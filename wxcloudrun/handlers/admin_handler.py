import logging
import jwt
from datetime import datetime, timedelta
from flask import request
from wxcloudrun.response import make_succ_response, make_err_response

logger = logging.getLogger('log')

# JWT密钥
JWT_SECRET = "admin_secret_key"
JWT_ALGORITHM = "HS256"

# 硬编码的管理员凭据
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def admin_login():
    """
    管理员登录
    """
    try:
        data = request.get_json()
        logger.info("管理员登录请求: %s", data.get('username') if data else 'None')
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            logger.warn("管理员登录失败: 用户名或密码错误")
            return make_err_response("用户名或密码错误"), 401
        
        # 生成JWT token
        payload = {
            'username': username,
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response_data = {
            'token': token,
            'admin': {
                'username': username,
                'role': 'admin'
            }
        }
        
        logger.info("管理员登录成功")
        return make_succ_response(response_data, "登录成功"), 200
        
    except Exception as e:
        logger.error("❌ 管理员登录失败: %s", str(e), exc_info=True)
        return make_err_response(f"登录失败: {str(e)}"), 500

