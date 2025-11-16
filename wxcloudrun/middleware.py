"""
认证中间件
"""
import jwt
from functools import wraps
from flask import request, redirect, url_for
from wxcloudrun.handlers.admin_handler import JWT_SECRET, JWT_ALGORITHM

def require_admin_auth(f):
    """
    管理员认证装饰器
    验证 JWT token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取 token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            # 如果是页面请求，重定向到登录页
            if request.path.startswith('/admin/') and not request.path.endswith('/login'):
                return redirect('/admin/login')
            # 如果是 API 请求，返回 401
            from wxcloudrun.response import make_err_response
            return make_err_response("未授权，请先登录"), 401
        
        # 提取 token
        try:
            token = auth_header.replace('Bearer ', '')
        except:
            token = None
        
        if not token:
            if request.path.startswith('/admin/') and not request.path.endswith('/login'):
                return redirect('/admin/login')
            from wxcloudrun.response import make_err_response
            return make_err_response("无效的 token"), 401
        
        # 验证 token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            # 检查是否是管理员
            if payload.get('role') != 'admin':
                if request.path.startswith('/admin/') and not request.path.endswith('/login'):
                    return redirect('/admin/login')
                from wxcloudrun.response import make_err_response
                return make_err_response("权限不足"), 403
            
            # 将管理员信息添加到 request
            request.admin = payload
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            if request.path.startswith('/admin/') and not request.path.endswith('/login'):
                return redirect('/admin/login')
            from wxcloudrun.response import make_err_response
            return make_err_response("Token 已过期"), 401
        except jwt.InvalidTokenError:
            if request.path.startswith('/admin/') and not request.path.endswith('/login'):
                return redirect('/admin/login')
            from wxcloudrun.response import make_err_response
            return make_err_response("无效的 token"), 401
    
    return decorated_function


def get_admin_from_request():
    """
    从请求中获取管理员信息（不强制要求认证）
    用于页面渲染时获取管理员信息
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        # 尝试从 cookie 或 session 获取（如果使用 cookie 存储 token）
        return None
    
    try:
        token = auth_header.replace('Bearer ', '')
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('role') == 'admin':
            return payload
    except:
        pass
    
    return None

