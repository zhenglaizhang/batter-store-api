-- 添加电池订单详情字段
-- 用于存储按重量提交的订单信息

ALTER TABLE battery_upload_orders 
ADD COLUMN order_type VARCHAR(50) DEFAULT 'photo_upload' NOT NULL COMMENT '订单类型：photo_upload-照片上传, weight_based-按重量计价',
ADD COLUMN batteries JSON NULL COMMENT '电池列表JSON数据',
ADD COLUMN total_price VARCHAR(50) NULL COMMENT '总价格',
ADD COLUMN total_weight VARCHAR(50) NULL COMMENT '总重量';

-- 添加注释
ALTER TABLE battery_upload_orders COMMENT = '电池上传订单表（已添加订单详情字段）';

