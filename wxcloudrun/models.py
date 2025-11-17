from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, BigInteger, ForeignKey, CheckConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from wxcloudrun import db
import uuid as uuid_lib


# 用户注册表
class UserRegistration(db.Model):
    __tablename__ = 'user_registrations'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    registration_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    business_type_id = Column(String(20), nullable=False)
    business_type_name = Column(String(50), nullable=False)
    user_role_id = Column(String(20), nullable=False)
    user_role_name = Column(String(50), nullable=False)
    store_name = Column(String(100), nullable=False)
    contact_name = Column(String(50), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    address = Column(String(300), nullable=False)
    business_license_path = Column(Text, nullable=True)
    status = Column(String(20), default='pending', nullable=False, index=True)
    submit_time = Column(DateTime, nullable=False)
    review_time = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='chk_status'),
    )


# 业务类型表
class BusinessType(db.Model):
    __tablename__ = 'business_types'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# 用户角色表
class UserRole(db.Model):
    __tablename__ = 'user_roles'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# 电池上传订单表
class BatteryUploadOrder(db.Model):
    __tablename__ = 'battery_upload_orders'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    user_id = Column(String(50), nullable=False, index=True)
    store_name = Column(String(255), nullable=False)
    contact_name = Column(String(100), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    contact_address = Column(Text, nullable=False)
    status = Column(String(50), default='pending', nullable=False, index=True)
    total_photos = Column(Integer, default=0, nullable=False)
    pickup_date = Column(DateTime, nullable=True)
    order_type = Column(String(50), default='photo_upload', nullable=False)  # photo_upload, weight_based
    batteries = Column(JSON, nullable=True)  # 电池列表JSON数据
    total_price = Column(String(50), nullable=True)  # 总价格（字符串格式，支持小数）
    total_weight = Column(String(50), nullable=True)  # 总重量（字符串格式，支持小数）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    photos = relationship('BatteryUploadPhoto', backref='order', cascade='all, delete-orphan')


# 电池上传照片表
class BatteryUploadPhoto(db.Model):
    __tablename__ = 'battery_upload_photos'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    order_id = Column(String(36), ForeignKey('battery_upload_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    upload_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

