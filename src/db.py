from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
from typing import Dict

db = dict(
    sql_type='mysql',
    user='wangzhihao',
    password='Wangzhihao_2021',
    host='10.10.1.217',
    port=3306,
    database='comcrawl_data',
)


def db_connect(_db: Dict) -> Engine:
    return create_engine(f"{_db.get('sql_type', 'mysql')}://"
                         f"{_db.get('user', 'root')}:{_db.get('password', '')}"
                         f"@{_db.get('host', 'localhost')}:{_db.get('port', 3306)}"
                         f"/{_db.get('database', '')}",
                         poolclass=NullPool)
