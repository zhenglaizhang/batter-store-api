# 创建应用实例
import sys
import logging
from wxcloudrun import app, db
from wxcloudrun import models
import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 启动Flask Web服务
if __name__ == '__main__':
    # 创建数据库表（如果不存在）
    with app.app_context():
        try:
            db.create_all()
            logger.info("数据库表创建/检查完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    # 启动服务器
    host = sys.argv[1] if len(sys.argv) > 1 else config.SERVER_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else config.SERVER_PORT
    logger.info(f"服务器启动在 {host}:{port}")
    app.run(host=host, port=port, debug=config.DEBUG)
