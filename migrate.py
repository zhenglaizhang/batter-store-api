#!/usr/bin/env python3
"""
数据库迁移脚本
执行 migrations/ 目录下的 SQL 迁移文件
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

def get_db_config():
    """获取数据库配置"""
    username = os.environ.get("MYSQL_USERNAME", "battery_user")
    password = os.environ.get("MYSQL_PASSWORD", "password")
    db_address = os.environ.get("MYSQL_ADDRESS", "localhost:3306")
    database_name = os.environ.get("MYSQL_DATABASE", "battery_recycling")
    
    # 解析地址
    if ':' in db_address:
        host, port = db_address.split(':')
        port = int(port)
    else:
        host = db_address
        port = 3306
    
    return {
        'host': host,
        'port': port,
        'user': username,
        'password': password,
        'database': database_name,
        'charset': 'utf8mb4'
    }

def execute_migration(migration_file):
    """执行单个迁移文件"""
    print(f"\n{'='*60}")
    print(f"执行迁移: {migration_file.name}")
    print(f"{'='*60}")
    
    try:
        # 读取SQL文件
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 连接数据库
        config = get_db_config()
        connection = pymysql.connect(**config)
        
        try:
            with connection.cursor() as cursor:
                # 执行SQL（支持多语句）
                for statement in sql_content.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cursor.execute(statement)
                            print(f"✓ 执行成功: {statement[:50]}...")
                        except Exception as e:
                            # 如果是"字段已存在"的错误，可以忽略
                            if 'Duplicate column name' in str(e) or 'already exists' in str(e).lower():
                                print(f"⚠ 字段已存在，跳过: {statement[:50]}...")
                            else:
                                print(f"✗ 执行失败: {e}")
                                print(f"  SQL: {statement[:100]}...")
                                raise
            
            # 提交事务
            connection.commit()
            print(f"✅ 迁移完成: {migration_file.name}")
            return True
            
        finally:
            connection.close()
            
    except Exception as e:
        print(f"❌ 迁移失败: {migration_file.name}")
        print(f"   错误: {str(e)}")
        return False

def main():
    """主函数"""
    # 获取迁移文件目录
    migrations_dir = Path(__file__).parent / 'migrations'
    
    if not migrations_dir.exists():
        print(f"❌ 迁移目录不存在: {migrations_dir}")
        sys.exit(1)
    
    # 获取所有迁移文件并按名称排序
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    if not migration_files:
        print("❌ 未找到迁移文件")
        sys.exit(1)
    
    print(f"找到 {len(migration_files)} 个迁移文件:")
    for f in migration_files:
        print(f"  - {f.name}")
    
    # 执行迁移
    success_count = 0
    for migration_file in migration_files:
        if execute_migration(migration_file):
            success_count += 1
        else:
            print(f"\n⚠️  迁移 {migration_file.name} 失败，但继续执行其他迁移...")
    
    print(f"\n{'='*60}")
    print(f"迁移完成: {success_count}/{len(migration_files)} 成功")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

