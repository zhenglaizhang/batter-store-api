import logging
from datetime import datetime
from sqlalchemy.exc import OperationalError
from sqlalchemy import and_
from wxcloudrun import db
from wxcloudrun.models import (
    UserRegistration, BusinessType, UserRole,
    BatteryUploadOrder, BatteryUploadPhoto, User, SmsCode
)

# 初始化日志
logger = logging.getLogger('log')


# ========== 用户注册相关 ==========

def create_user_registration(registration_data):
    """
    创建用户注册记录
    :param registration_data: 注册数据字典
    :return: UserRegistration 实体
    """
    try:
        registration = UserRegistration(**registration_data)
        db.session.add(registration)
        db.session.commit()
        db.session.refresh(registration)
        return registration
    except OperationalError as e:
        logger.error("create_user_registration errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("create_user_registration errorMsg= {}".format(e))
        db.session.rollback()
        raise


def get_user_registration_by_user_id(user_id):
    """
    根据 user_id 查询用户注册记录
    :param user_id: 用户ID
    :return: UserRegistration 实体或 None
    """
    try:
        return UserRegistration.query.filter(UserRegistration.user_id == user_id).first()
    except OperationalError as e:
        logger.error("get_user_registration_by_user_id errorMsg= {}".format(e))
        return None


def get_user_registration_by_registration_id(registration_id):
    """
    根据 registration_id 查询用户注册记录
    :param registration_id: 注册ID
    :return: UserRegistration 实体或 None
    """
    try:
        return UserRegistration.query.filter(
            UserRegistration.registration_id == registration_id
        ).first()
    except OperationalError as e:
        logger.error("get_user_registration_by_registration_id errorMsg= {}".format(e))
        return None


def get_user_registration_by_phone(phone):
    """
    根据手机号查询用户注册记录（返回最新的）
    :param phone: 手机号
    :return: UserRegistration 实体或 None
    """
    try:
        return UserRegistration.query.filter(
            UserRegistration.contact_phone == phone
        ).order_by(UserRegistration.created_at.desc()).first()
    except OperationalError as e:
        logger.error("get_user_registration_by_phone errorMsg= {}".format(e))
        return None
    except Exception as e:
        logger.error("get_user_registration_by_phone errorMsg= {}".format(e))
        return None


def get_latest_user_registration():
    """
    获取最新的用户注册记录
    :return: UserRegistration 实体或 None
    """
    try:
        return UserRegistration.query.order_by(
            UserRegistration.created_at.desc()
        ).first()
    except OperationalError as e:
        logger.error("get_latest_user_registration errorMsg= {}".format(e))
        return None


def get_all_user_registrations():
    """
    获取所有用户注册记录
    :return: UserRegistration 列表
    """
    try:
        return UserRegistration.query.order_by(
            UserRegistration.created_at.desc()
        ).all()
    except OperationalError as e:
        logger.error("get_all_user_registrations errorMsg= {}".format(e))
        return []


def update_user_registration_status(registration_id, status, review_comment=None):
    """
    更新用户注册状态
    :param registration_id: 注册ID
    :param status: 新状态
    :param review_comment: 审核评论
    :return: 更新后的 UserRegistration 实体或 None
    """
    try:
        from datetime import datetime
        registration = get_user_registration_by_registration_id(registration_id)
        if registration is None:
            return None
        
        registration.status = status
        registration.review_time = datetime.utcnow()
        if review_comment:
            registration.review_comment = review_comment
        registration.updated_at = datetime.utcnow()
        
        db.session.commit()
        db.session.refresh(registration)
        return registration
    except OperationalError as e:
        logger.error("update_user_registration_status errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("update_user_registration_status errorMsg= {}".format(e))
        db.session.rollback()
        raise


def update_user_business_license_path(user_id, business_license_path):
    """
    更新用户营业执照路径
    :param user_id: 用户ID
    :param business_license_path: 营业执照路径
    :return: 是否更新成功
    """
    try:
        from datetime import datetime
        registration = get_user_registration_by_user_id(user_id)
        if registration is None:
            return False
        
        registration.business_license_path = business_license_path
        registration.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    except OperationalError as e:
        logger.error("update_user_business_license_path errorMsg= {}".format(e))
        db.session.rollback()
        return False
    except Exception as e:
        logger.error("update_user_business_license_path errorMsg= {}".format(e))
        db.session.rollback()
        return False


# ========== 电池订单相关 ==========

def create_battery_upload_order(order_data):
    """
    创建电池上传订单
    :param order_data: 订单数据字典
    :return: BatteryUploadOrder 实体
    """
    try:
        order = BatteryUploadOrder(**order_data)
        db.session.add(order)
        db.session.commit()
        db.session.refresh(order)
        return order
    except OperationalError as e:
        logger.error("create_battery_upload_order errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("create_battery_upload_order errorMsg= {}".format(e))
        db.session.rollback()
        raise


def get_battery_upload_order_by_id(order_id):
    """
    根据订单ID查询电池上传订单
    :param order_id: 订单ID
    :return: BatteryUploadOrder 实体或 None
    """
    try:
        return BatteryUploadOrder.query.filter(BatteryUploadOrder.id == order_id).first()
    except OperationalError as e:
        logger.error("get_battery_upload_order_by_id errorMsg= {}".format(e))
        return None


def get_all_battery_upload_orders():
    """
    获取所有电池上传订单
    :return: BatteryUploadOrder 列表
    """
    try:
        return BatteryUploadOrder.query.order_by(
            BatteryUploadOrder.created_at.desc()
        ).all()
    except OperationalError as e:
        logger.error("get_all_battery_upload_orders errorMsg= {}".format(e))
        return []


def update_battery_upload_order(order_id, update_data):
    """
    更新电池上传订单
    :param order_id: 订单ID
    :param update_data: 要更新的数据字典
    :return: 更新后的 BatteryUploadOrder 实体或 None
    """
    try:
        order = get_battery_upload_order_by_id(order_id)
        if order is None:
            return None
        
        # 更新字段
        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        db.session.refresh(order)
        return order
    except OperationalError as e:
        logger.error("update_battery_upload_order errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("update_battery_upload_order errorMsg= {}".format(e))
        db.session.rollback()
        raise


def create_battery_upload_photo(photo_data):
    """
    创建电池上传照片记录
    :param photo_data: 照片数据字典
    :return: BatteryUploadPhoto 实体
    """
    try:
        photo = BatteryUploadPhoto(**photo_data)
        db.session.add(photo)
        db.session.commit()
        db.session.refresh(photo)
        return photo
    except OperationalError as e:
        logger.error("create_battery_upload_photo errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("create_battery_upload_photo errorMsg= {}".format(e))
        db.session.rollback()
        raise


def get_photos_by_order_id(order_id):
    """
    根据订单ID获取所有照片
    :param order_id: 订单ID
    :return: BatteryUploadPhoto 列表
    """
    try:
        return BatteryUploadPhoto.query.filter(
            BatteryUploadPhoto.order_id == order_id
        ).order_by(BatteryUploadPhoto.upload_index).all()
    except OperationalError as e:
        logger.error("get_photos_by_order_id errorMsg= {}".format(e))
        return []


# ========== 业务类型和用户角色 ==========

def get_business_type_by_id(business_type_id):
    """
    根据ID查询业务类型
    :param business_type_id: 业务类型ID
    :return: BusinessType 实体或 None
    """
    try:
        return BusinessType.query.filter(BusinessType.id == business_type_id).first()
    except OperationalError as e:
        logger.error("get_business_type_by_id errorMsg= {}".format(e))
        return None


def get_user_role_by_id(user_role_id):
    """
    根据ID查询用户角色
    :param user_role_id: 用户角色ID
    :return: UserRole 实体或 None
    """
    try:
        return UserRole.query.filter(UserRole.id == user_role_id).first()
    except OperationalError as e:
        logger.error("get_user_role_by_id errorMsg= {}".format(e))
        return None


# ========== 计数器相关（保留原有功能） ==========

def query_counterbyid(counter_id):
    """
    根据ID查询计数器
    :param counter_id: 计数器ID
    :return: Counters 实体或 None
    """
    try:
        from wxcloudrun.model import Counters
        return Counters.query.filter(Counters.id == counter_id).first()
    except OperationalError as e:
        logger.error("query_counterbyid errorMsg= {}".format(e))
        return None
    except Exception as e:
        logger.error("query_counterbyid errorMsg= {}".format(e))
        return None


def insert_counter(counter):
    """
    插入计数器
    :param counter: Counters 实体
    :return: 是否成功
    """
    try:
        db.session.add(counter)
        db.session.commit()
        return True
    except OperationalError as e:
        logger.error("insert_counter errorMsg= {}".format(e))
        db.session.rollback()
        return False
    except Exception as e:
        logger.error("insert_counter errorMsg= {}".format(e))
        db.session.rollback()
        return False


def update_counterbyid(counter):
    """
    更新计数器
    :param counter: Counters 实体
    :return: 是否成功
    """
    try:
        db.session.commit()
        return True
    except OperationalError as e:
        logger.error("update_counterbyid errorMsg= {}".format(e))
        db.session.rollback()
        return False
    except Exception as e:
        logger.error("update_counterbyid errorMsg= {}".format(e))
        db.session.rollback()
        return False


def delete_counterbyid(counter_id):
    """
    根据ID删除计数器
    :param counter_id: 计数器ID
    :return: 是否成功
    """
    try:
        from wxcloudrun.model import Counters
        counter = Counters.query.filter(Counters.id == counter_id).first()
        if counter:
            db.session.delete(counter)
            db.session.commit()
        return True
    except OperationalError as e:
        logger.error("delete_counterbyid errorMsg= {}".format(e))
        db.session.rollback()
        return False
    except Exception as e:
        logger.error("delete_counterbyid errorMsg= {}".format(e))
        db.session.rollback()
        return False


# ========== 用户和短信验证码相关 ==========

def get_user_by_phone(phone):
    """
    根据手机号查询用户
    :param phone: 手机号
    :return: User 实体或 None
    """
    try:
        return User.query.filter(User.phone == phone).first()
    except OperationalError as e:
        logger.error("get_user_by_phone errorMsg= {}".format(e))
        return None
    except Exception as e:
        logger.error("get_user_by_phone errorMsg= {}".format(e))
        return None


def create_user(phone):
    """
    创建用户
    :param phone: 手机号
    :return: User 实体
    """
    try:
        user = User(phone=phone)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user
    except OperationalError as e:
        logger.error("create_user errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("create_user errorMsg= {}".format(e))
        db.session.rollback()
        raise


def create_sms_code(phone, code, ip_address=None):
    """
    创建短信验证码记录
    :param phone: 手机号
    :param code: 验证码
    :param ip_address: IP地址
    :return: SmsCode 实体
    """
    try:
        sms_code = SmsCode(phone=phone, code=code, ip_address=ip_address)
        db.session.add(sms_code)
        db.session.commit()
        db.session.refresh(sms_code)
        return sms_code
    except OperationalError as e:
        logger.error("create_sms_code errorMsg= {}".format(e))
        db.session.rollback()
        raise
    except Exception as e:
        logger.error("create_sms_code errorMsg= {}".format(e))
        db.session.rollback()
        raise


def get_latest_sms_code(phone):
    """
    获取指定手机号最新的验证码（未使用且未过期）
    :param phone: 手机号
    :return: SmsCode 实体或 None
    """
    try:
        from datetime import datetime, timedelta
        # 验证码有效期5分钟
        expire_time = datetime.utcnow() - timedelta(minutes=5)
        return SmsCode.query.filter(
            and_(
                SmsCode.phone == phone,
                SmsCode.used_at.is_(None),
                SmsCode.sent_at >= expire_time
            )
        ).order_by(SmsCode.sent_at.desc()).first()
    except OperationalError as e:
        logger.error("get_latest_sms_code errorMsg= {}".format(e))
        return None
    except Exception as e:
        logger.error("get_latest_sms_code errorMsg= {}".format(e))
        return None


def mark_sms_code_as_used(sms_code_id):
    """
    标记验证码为已使用
    :param sms_code_id: 验证码ID
    :return: 是否成功
    """
    try:
        from datetime import datetime
        sms_code = SmsCode.query.filter(SmsCode.id == sms_code_id).first()
        if sms_code:
            sms_code.used_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except OperationalError as e:
        logger.error("mark_sms_code_as_used errorMsg= {}".format(e))
        db.session.rollback()
        return False
    except Exception as e:
        logger.error("mark_sms_code_as_used errorMsg= {}".format(e))
        db.session.rollback()
        return False
