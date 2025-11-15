import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any


# 手机号验证正则表达式
PHONE_REGEX = re.compile(r'^1[3-9]\d{9}$')


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    :param phone: 手机号
    :return: 是否有效
    """
    return bool(PHONE_REGEX.match(phone))


def generate_user_id() -> str:
    """
    生成用户ID
    :return: 用户ID字符串
    """
    return f"user_{uuid.uuid4()}"


def generate_registration_id() -> str:
    """
    生成注册ID
    :return: 注册ID字符串
    """
    return f"reg_{uuid.uuid4()}"


def is_valid_image_type(filename: str) -> bool:
    """
    验证是否为有效的图片类型
    :param filename: 文件名
    :return: 是否有效
    """
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']


def get_mime_type(extension: str) -> str:
    """
    获取MIME类型
    :param extension: 文件扩展名
    :return: MIME类型字符串
    """
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')


def validate_user_registration_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    验证用户注册数据
    :param data: 注册数据字典
    :return: (是否有效, 错误消息)
    """
    # 验证业务类型
    if not data.get('business_type') or len(data['business_type']) < 1 or len(data['business_type']) > 50:
        return False, "业务类型名称长度必须在1-50字符之间"
    
    if not data.get('business_type_id') or len(data['business_type_id']) < 1 or len(data['business_type_id']) > 20:
        return False, "业务类型ID长度必须在1-20字符之间"
    
    # 验证用户角色
    if not data.get('user_role') or len(data['user_role']) < 1 or len(data['user_role']) > 50:
        return False, "用户角色名称长度必须在1-50字符之间"
    
    if not data.get('user_role_id') or len(data['user_role_id']) < 1 or len(data['user_role_id']) > 20:
        return False, "用户角色ID长度必须在1-20字符之间"
    
    # 验证用户信息
    user_info = data.get('user_info', {})
    if not user_info:
        return False, "缺少用户信息"
    
    if not user_info.get('store_name') or len(user_info['store_name']) < 1 or len(user_info['store_name']) > 50:
        return False, "店名长度必须在1-50字符之间"
    
    if not user_info.get('contact_name') or len(user_info['contact_name']) < 1 or len(user_info['contact_name']) > 20:
        return False, "联系人姓名长度必须在1-20字符之间"
    
    if not user_info.get('contact_phone') or not validate_phone(user_info['contact_phone']):
        return False, "手机号格式不正确"
    
    if not user_info.get('address') or len(user_info['address']) < 1 or len(user_info['address']) > 200:
        return False, "地址长度必须在1-200字符之间"
    
    return True, None

