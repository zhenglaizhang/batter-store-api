-- 添加营业执照字段到用户注册表
ALTER TABLE user_registrations 
ADD COLUMN business_license_path TEXT NULL;

-- 添加注释
ALTER TABLE user_registrations MODIFY COLUMN business_license_path TEXT NULL COMMENT '营业执照照片文件路径';
