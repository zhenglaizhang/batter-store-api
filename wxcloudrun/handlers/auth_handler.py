"""
短信验证码认证处理器
"""
import logging
import random
import jwt
from datetime import datetime, timedelta
from flask import request
from wxcloudrun import db
from wxcloudrun.dao import (
    get_user_by_phone, create_user, create_sms_code,
    get_latest_sms_code, mark_sms_code_as_used
)
from wxcloudrun.utils import validate_phone
from wxcloudrun.response import make_succ_response, make_err_response

logger = logging.getLogger('log')

# Mock验证码（固定返回123456）
MOCK_SMS_CODE = '123456'

# JWT配置（用户认证，区别于管理员）
USER_JWT_SECRET = "user_secret_key_change_in_production"
USER_JWT_ALGORITHM = "HS256"


def send_sms_code():
    """
    发送短信验证码（Mock版本）
    """
    try:
        logger.info("🚀 开始处理发送短信验证码请求")
        data = request.get_json()
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        phone = data.get('phone', '').strip()
        
        # 验证手机号格式
        if not phone:
            return make_err_response("手机号不能为空"), 400
        
        if not validate_phone(phone):
            return make_err_response("手机号格式不正确"), 400
        
        # 检查发送频率（1分钟内不能重复发送）
        latest_code = get_latest_sms_code(phone)
        if latest_code:
            time_diff = datetime.utcnow() - latest_code.sent_at
            if time_diff.total_seconds() < 60:
                remaining_seconds = 60 - int(time_diff.total_seconds())
                return make_err_response(f"验证码发送过于频繁，请{remaining_seconds}秒后再试"), 429
        
        # 生成验证码（Mock版本，固定返回123456）
        code = MOCK_SMS_CODE
        
        # 获取客户端IP
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0]
        
        # 保存验证码到数据库
        create_sms_code(phone, code, ip_address)
        
        logger.info("✅ 短信验证码发送成功: phone=%s, code=%s", phone, code)
        
        # Mock响应，不返回真实验证码
        return make_succ_response(
            {"message": "验证码已发送，请注意查收"},
            "验证码发送成功"
        ), 200
        
    except Exception as e:
        logger.error("❌ 发送短信验证码失败: %s", str(e), exc_info=True)
        return make_err_response(f"发送验证码失败: {str(e)}"), 500


def verify_sms_code():
    """
    验证短信验证码
    """
    try:
        logger.info("🚀 开始处理验证短信验证码请求")
        data = request.get_json()
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        
        # 验证参数
        if not phone:
            return make_err_response("手机号不能为空"), 400
        
        if not code:
            return make_err_response("验证码不能为空"), 400
        
        if not validate_phone(phone):
            return make_err_response("手机号格式不正确"), 400
        
        # 获取最新的未使用验证码
        sms_code_record = get_latest_sms_code(phone)
        
        if not sms_code_record:
            return make_err_response("验证码不存在或已过期，请重新获取"), 400
        
        # 验证验证码
        if sms_code_record.code != code:
            logger.warning("⚠️ 验证码错误: phone=%s, input_code=%s, correct_code=%s", 
                          phone, code, sms_code_record.code)
            return make_err_response("验证码错误"), 400
        
        # 标记验证码为已使用
        mark_sms_code_as_used(sms_code_record.id)
        
        logger.info("✅ 短信验证码验证成功: phone=%s", phone)
        
        return make_succ_response(
            {"verified": True, "phone": phone},
            "验证码验证成功"
        ), 200
        
    except Exception as e:
        logger.error("❌ 验证短信验证码失败: %s", str(e), exc_info=True)
        return make_err_response(f"验证验证码失败: {str(e)}"), 500


def login_with_sms():
    """
    使用手机号和验证码登录
    """
    try:
        logger.info("🚀 开始处理短信验证码登录请求")
        data = request.get_json()
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        
        # 验证参数
        if not phone:
            return make_err_response("手机号不能为空"), 400
        
        if not code:
            return make_err_response("验证码不能为空"), 400
        
        if not validate_phone(phone):
            return make_err_response("手机号格式不正确"), 400
        
        # 验证验证码
        sms_code_record = get_latest_sms_code(phone)
        
        if not sms_code_record:
            return make_err_response("验证码不存在或已过期，请重新获取"), 400
        
        if sms_code_record.code != code:
            logger.warning("⚠️ 登录验证码错误: phone=%s", phone)
            return make_err_response("验证码错误"), 400
        
        # 标记验证码为已使用
        mark_sms_code_as_used(sms_code_record.id)
        
        # 查找用户（不自动创建）
        user = get_user_by_phone(phone)
        if not user:
            logger.warning("⚠️ 登录失败：手机号不存在: phone=%s", phone)
            return make_err_response("该手机号尚未注册，请先完成注册"), 404
        
        logger.info("✅ 用户登录成功: phone=%s, user_id=%s", phone, user.id)
        
        # 生成JWT token
        payload = {
            'user_id': str(user.id),
            'phone': user.phone,
            'role': 'user',
            'exp': datetime.utcnow() + timedelta(days=7)  # token有效期7天
        }
        
        token = jwt.encode(payload, USER_JWT_SECRET, algorithm=USER_JWT_ALGORITHM)
        # 确保 token 是字符串（Python 3 中 jwt.encode 可能返回字节）
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        # 构建响应数据
        response_data = {
            "token": token,
            "user_id": str(user.id),
            "phone": user.phone,
            "created_at": user.created_at.isoformat() + 'Z' if user.created_at else None,
        }
        
        logger.info("🎉 短信验证码登录处理完成，已生成token")
        return make_succ_response(response_data, "登录成功"), 200
        
    except Exception as e:
        logger.error("❌ 短信验证码登录失败: %s", str(e), exc_info=True)
        return make_err_response(f"登录失败: {str(e)}"), 500

