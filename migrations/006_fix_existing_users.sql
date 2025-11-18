-- 为已注册的用户创建 User 记录
-- 从 user_registrations 表中获取所有唯一的手机号，并在 users 表中创建对应的记录

INSERT INTO users (phone, created_at, updated_at)
SELECT DISTINCT 
    contact_phone as phone,
    MIN(created_at) as created_at,
    MAX(updated_at) as updated_at
FROM user_registrations
WHERE contact_phone NOT IN (SELECT phone FROM users)
GROUP BY contact_phone
ON DUPLICATE KEY UPDATE updated_at = VALUES(updated_at);

