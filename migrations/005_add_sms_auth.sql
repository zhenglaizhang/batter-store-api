-- 用户表（用于短信验证码登录）
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(11) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 短信验证码表
CREATE TABLE IF NOT EXISTS sms_codes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(11) NOT NULL,
    code VARCHAR(6) NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used_at DATETIME NULL,
    ip_address VARCHAR(45) NULL,
    INDEX idx_sms_codes_phone (phone),
    INDEX idx_sms_codes_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

