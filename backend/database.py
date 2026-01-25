from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# 构建数据库 URL
# 格式: mysql+pymysql://user:password@host:port/database?charset=utf8mb4
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}"

# 创建数据库引擎，配置连接池
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    pool_pre_ping=True,  # 每次获取连接时检查有效性 (自动重连)
    pool_recycle=3600    # 连接回收时间 (秒)
)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 Base 类供模型继承
Base = declarative_base()

def get_db():
    """
    Dependency for FastAPI routers to get a database session.
    Closes the session after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
