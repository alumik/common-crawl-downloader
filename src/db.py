import dataclasses
import configparser

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool


@dataclasses.dataclass
class DatabaseConfig:
    drivername: str = 'mysql'
    username: str = 'root'
    password: str = ''
    host: str = 'localhost'
    port: int = 3306
    database: str = ''


def get_database_config(config: configparser.ConfigParser) -> DatabaseConfig:
    return DatabaseConfig(
        drivername=config.get('database', 'drivername'),
        username=config.get('database', 'username'),
        password=config.get('database', 'password'),
        host=config.get('database', 'host'),
        port=config.getint('database', 'port'),
        database=config.get('database', 'database'),
    )


def db_connect(conf: DatabaseConfig) -> Engine:
    return create_engine(f"{conf.drivername}://{conf.username}:{conf.password}@{conf.host}:{conf.port}/{conf.database}",
                         poolclass=NullPool)
