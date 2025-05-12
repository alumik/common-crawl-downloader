from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

import configs


def db_connect(config: configs.Config) -> Engine:
    drivername = config.database.drivername
    username = config.database.username
    password = config.database.password
    host = config.database.host
    port = config.database.port
    database = config.database.database
    return create_engine(f'{drivername}://{username}:{password}@{host}:{port}/{database}', poolclass=NullPool)
