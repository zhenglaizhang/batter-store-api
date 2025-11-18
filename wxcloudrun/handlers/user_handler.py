import logging
from datetime import datetime
from flask import request, jsonify
from wxcloudrun import db
from wxcloudrun.dao import (
    create_user_registration, get_latest_user_registration,
    get_all_user_registrations, update_user_registration_status,
    get_user_registration_by_user_id, get_latest_sms_code, mark_sms_code_as_used
)
from wxcloudrun.utils import (
    generate_user_id, generate_registration_id, validate_user_registration_data
)
from wxcloudrun.response import make_succ_response, make_err_response

logger = logging.getLogger('log')


def register_user():
    """
    用户注册处理器
    """
    try:
        logger.info("🚀 开始处理用户注册请求")
        data = request.get_json()
        logger.info("📋 请求数据: %s", data)
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        # 验证数据
        is_valid, error_msg = validate_user_registration_data(data)
        if not is_valid:
            logger.error("❌ 数据验证失败: %s", error_msg)
            return make_err_response(error_msg), 422
        
        # 验证短信验证码
        phone = data['user_info']['contact_phone']
        sms_code = data.get('sms_code', '').strip()
        
        if not sms_code:
            logger.error("❌ 缺少短信验证码")
            return make_err_response("请先获取并输入短信验证码"), 400
        
        # 获取最新的未使用验证码
        sms_code_record = get_latest_sms_code(phone)
        
        if not sms_code_record:
            logger.error("❌ 验证码不存在或已过期: phone=%s", phone)
            return make_err_response("验证码不存在或已过期，请重新获取"), 400
        
        # 验证验证码
        if sms_code_record.code != sms_code:
            logger.warning("⚠️ 注册验证码错误: phone=%s, input_code=%s", phone, sms_code)
            return make_err_response("验证码错误"), 400
        
        # 标记验证码为已使用
        mark_sms_code_as_used(sms_code_record.id)
        logger.info("✅ 短信验证码验证通过: phone=%s", phone)
        
        logger.info("✅ 数据验证通过，开始处理注册")
        
        # 生成唯一ID
        user_id = generate_user_id()
        registration_id = generate_registration_id()
        logger.info("🆔 生成ID: user_id=%s, registration_id=%s", user_id, registration_id)
        
        # 解析提交时间
        submit_time = datetime.utcnow()
        if 'submit_time' in data:
            try:
                submit_time = datetime.fromisoformat(data['submit_time'].replace('Z', '+00:00'))
            except:
                pass
        
        # 构建注册数据
        user_info = data['user_info']
        registration_data = {
            'registration_id': registration_id,
            'user_id': user_id,
            'business_type_id': data['business_type_id'],
            'business_type_name': data['business_type'],
            'user_role_id': data['user_role_id'],
            'user_role_name': data['user_role'],
            'store_name': user_info['store_name'],
            'contact_name': user_info['contact_name'],
            'contact_phone': user_info['contact_phone'],
            'address': user_info['address'],
            'business_license_path': user_info.get('business_license'),
            'status': 'pending',
            'submit_time': submit_time,
        }
        
        logger.info("💾 开始数据库操作...")
        registration = create_user_registration(registration_data)
        
        logger.info("✅ 数据库操作成功: user_id=%s, registration_id=%s", user_id, registration_id)
        
        # 构建响应
        response_data = {
            'user_id': user_id,
            'registration_id': registration_id,
            'status': 'pending',
            'submit_time': submit_time.isoformat() + 'Z',
            'estimated_review_time': '1-3个工作日'
        }
        
        logger.info("🎉 用户注册处理完成")
        return make_succ_response(response_data, "注册成功"), 200
        
    except Exception as e:
        logger.error("❌ 用户注册失败: %s", str(e), exc_info=True)
        return make_err_response(f"注册失败: {str(e)}"), 500


def get_user_profile():
    """
    获取用户个人信息处理器
    默认返回最新插入的注册用户数据
    """
    try:
        logger.info("🚀 开始处理获取用户个人信息请求")
        
        user_profile = get_latest_user_registration()
        
        if user_profile is None:
            logger.warn("⚠️ 未找到任何用户注册记录")
            return make_err_response("未找到用户信息"), 404
        
        logger.info("✅ 成功获取用户个人信息: user_id=%s", user_profile.user_id)
        
        # 构建响应数据
        response_data = {
            'user_id': user_profile.user_id,
            'registration_id': user_profile.registration_id,
            'business_type_id': user_profile.business_type_id,
            'business_type_name': user_profile.business_type_name,
            'user_role_id': user_profile.user_role_id,
            'user_role_name': user_profile.user_role_name,
            'store_name': user_profile.store_name,
            'contact_name': user_profile.contact_name,
            'contact_phone': user_profile.contact_phone,
            'address': user_profile.address,
            'business_license_path': user_profile.business_license_path,
            'status': user_profile.status,
            'submit_time': user_profile.submit_time.isoformat() + 'Z' if user_profile.submit_time else None,
            'review_time': user_profile.review_time.isoformat() + 'Z' if user_profile.review_time else None,
            'review_comment': user_profile.review_comment,
            'created_at': user_profile.created_at.isoformat() + 'Z' if user_profile.created_at else None,
            'updated_at': user_profile.updated_at.isoformat() + 'Z' if user_profile.updated_at else None,
        }
        
        return make_succ_response(response_data, "获取用户个人信息成功"), 200
        
    except Exception as e:
        logger.error("❌ 获取用户个人信息失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取用户信息失败: {str(e)}"), 500


def get_all_user_registrations_handler():
    """
    获取所有用户注册记录（管理员功能）
    """
    try:
        logger.info("🚀 开始获取所有用户注册记录")
        
        registrations = get_all_user_registrations()
        logger.info("✅ 成功获取用户注册记录，共 %d 条", len(registrations))
        
        # 构建响应数据
        response_data = []
        for reg in registrations:
            response_data.append({
                'user_id': reg.user_id,
                'registration_id': reg.registration_id,
                'business_type_id': reg.business_type_id,
                'business_type_name': reg.business_type_name,
                'user_role_id': reg.user_role_id,
                'user_role_name': reg.user_role_name,
                'store_name': reg.store_name,
                'contact_name': reg.contact_name,
                'contact_phone': reg.contact_phone,
                'address': reg.address,
                'business_license_path': reg.business_license_path,
                'status': reg.status,
                'submit_time': reg.submit_time.isoformat() + 'Z' if reg.submit_time else None,
                'review_time': reg.review_time.isoformat() + 'Z' if reg.review_time else None,
                'review_comment': reg.review_comment,
                'created_at': reg.created_at.isoformat() + 'Z' if reg.created_at else None,
                'updated_at': reg.updated_at.isoformat() + 'Z' if reg.updated_at else None,
            })
        
        return make_succ_response(response_data, "获取用户注册记录成功"), 200
        
    except Exception as e:
        logger.error("❌ 获取用户注册记录失败: %s", str(e), exc_info=True)
        return make_err_response(f"获取用户注册记录失败: {str(e)}"), 500


def update_user_registration_status_handler(registration_id):
    """
    更新用户注册状态（管理员功能）
    """
    try:
        logger.info("🚀 开始更新用户注册状态: %s", registration_id)
        data = request.get_json()
        logger.info("📋 更新数据: %s", data)
        
        if not data:
            return make_err_response("请求数据不能为空"), 400
        
        status = data.get('status')
        review_comment = data.get('review_comment')
        
        # 验证状态值
        if status not in ['pending', 'approved', 'rejected']:
            return make_err_response("无效的状态值，必须是 pending、approved 或 rejected"), 400
        
        # 更新状态
        updated_registration = update_user_registration_status(
            registration_id, status, review_comment
        )
        
        if updated_registration is None:
            logger.warn("⚠️ 未找到指定的注册记录: %s", registration_id)
            return make_err_response("未找到指定的注册记录"), 404
        
        logger.info("✅ 成功更新用户注册状态: %s", updated_registration.user_id)
        
        # 构建响应数据
        response_data = {
            'user_id': updated_registration.user_id,
            'registration_id': updated_registration.registration_id,
            'business_type_id': updated_registration.business_type_id,
            'business_type_name': updated_registration.business_type_name,
            'user_role_id': updated_registration.user_role_id,
            'user_role_name': updated_registration.user_role_name,
            'store_name': updated_registration.store_name,
            'contact_name': updated_registration.contact_name,
            'contact_phone': updated_registration.contact_phone,
            'address': updated_registration.address,
            'business_license_path': updated_registration.business_license_path,
            'status': updated_registration.status,
            'submit_time': updated_registration.submit_time.isoformat() + 'Z' if updated_registration.submit_time else None,
            'review_time': updated_registration.review_time.isoformat() + 'Z' if updated_registration.review_time else None,
            'review_comment': updated_registration.review_comment,
            'created_at': updated_registration.created_at.isoformat() + 'Z' if updated_registration.created_at else None,
            'updated_at': updated_registration.updated_at.isoformat() + 'Z' if updated_registration.updated_at else None,
        }
        
        return make_succ_response(response_data, "更新用户注册状态成功"), 200
        
    except Exception as e:
        logger.error("❌ 更新用户注册状态失败: %s", str(e), exc_info=True)
        return make_err_response(f"更新用户注册状态失败: {str(e)}"), 500

