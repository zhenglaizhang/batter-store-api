from datetime import datetime
from flask import render_template, request, send_from_directory, redirect, url_for
import os
from wxcloudrun import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.handlers import user_handler, upload_handler, admin_handler, auth_handler
from wxcloudrun.middleware import require_admin_auth, require_user_auth


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


# ========== 原有计数器API（保留） ==========

@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 10
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


# ========== 用户相关API ==========

@app.route('/api/user/register', methods=['POST'])
def register_user():
    """用户注册"""
    return user_handler.register_user()


# ========== 短信验证码认证相关API ==========

@app.route('/api/auth/sms/send', methods=['POST'])
def send_sms_code():
    """发送短信验证码"""
    return auth_handler.send_sms_code()


@app.route('/api/auth/sms/verify', methods=['POST'])
def verify_sms_code():
    """验证短信验证码"""
    return auth_handler.verify_sms_code()


@app.route('/api/auth/login', methods=['POST'])
def login_with_sms():
    """使用手机号和验证码登录"""
    return auth_handler.login_with_sms()


@app.route('/api/user/profile', methods=['GET'])
@require_user_auth
def get_user_profile():
    """获取用户个人信息（需要认证）"""
    return user_handler.get_user_profile()


@app.route('/api/user/registrations', methods=['GET'])
def get_all_user_registrations():
    """获取所有用户注册记录（管理员功能）"""
    return user_handler.get_all_user_registrations_handler()


@app.route('/api/user/registrations/<registration_id>/status', methods=['PUT'])
def update_user_registration_status(registration_id):
    """更新用户注册状态（管理员功能）"""
    return user_handler.update_user_registration_status_handler(registration_id)


# ========== 上传相关API ==========

@app.route('/api/upload/photos', methods=['POST'])
def upload_photos():
    """上传照片"""
    return upload_handler.upload_photos()


@app.route('/api/upload/photos', methods=['GET'])
def get_uploaded_photos():
    """获取上传的照片列表"""
    return upload_handler.get_uploaded_photos()


@app.route('/api/upload/business-license', methods=['POST'])
def upload_business_license():
    """上传营业执照"""
    return upload_handler.upload_business_license()


# ========== 电池订单相关API ==========

@app.route('/api/battery/orders', methods=['GET'])
def get_all_battery_orders():
    """获取所有电池上传订单（管理员功能）"""
    return upload_handler.get_all_battery_orders()


@app.route('/api/battery/orders', methods=['POST'])
def create_battery_order():
    """创建电池订单"""
    return upload_handler.create_battery_order()


@app.route('/api/battery/orders/<order_id>', methods=['GET'])
def get_battery_order_detail(order_id):
    """获取电池上传订单详情（管理员功能）"""
    return upload_handler.get_battery_order_detail(order_id)


@app.route('/api/battery/orders/<order_id>', methods=['PUT'])
# TODO: 暂时禁用授权检查，以便小程序可以编辑订单。以后需要实现小程序用户认证机制
# @require_admin_auth
def update_battery_order(order_id):
    """更新电池订单信息（管理员功能，支持编辑）"""
    return upload_handler.update_battery_order(order_id)


# ========== 管理员相关API ==========

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    return admin_handler.admin_login()


# ========== 管理后台页面路由 ==========

@app.route('/admin/login')
def admin_login_page():
    """管理员登录页面"""
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    """管理员退出登录（清除 session，前端会清除 localStorage）"""
    return redirect('/admin/login')


@app.route('/admin/dashboard')
def admin_dashboard():
    """管理后台首页"""
    return render_template('admin/dashboard.html')


@app.route('/admin/user-review')
def admin_user_review():
    """用户注册审核页面"""
    return render_template('admin/user-review.html')


@app.route('/admin/order-tracking')
def admin_order_tracking():
    """电池订单跟踪页面"""
    return render_template('admin/order-tracking.html')


# ========== 静态文件服务 ==========

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    upload_dir = os.path.join(os.getcwd(), 'uploads')
    return send_from_directory(upload_dir, filename)
