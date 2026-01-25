-- 1. 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS schedule_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建专用应用用户 'schedule_user'，避免使用 root
-- 密码设置为: schedule_pass_2024
-- 使用 mysql_native_password 确保兼容性
CREATE USER IF NOT EXISTS 'schedule_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'schedule_pass_2024';
CREATE USER IF NOT EXISTS 'schedule_user'@'%' IDENTIFIED WITH mysql_native_password BY 'schedule_pass_2024';

-- 3. 授予权限
GRANT ALL PRIVILEGES ON schedule_db.* TO 'schedule_user'@'localhost';
GRANT ALL PRIVILEGES ON schedule_db.* TO 'schedule_user'@'%';

-- 4. 刷新权限
FLUSH PRIVILEGES;

-- 5. 如果必须使用 root 用户（不推荐），请在服务器手动执行以下命令修复 socket 认证问题：
-- ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '你的root密码';
