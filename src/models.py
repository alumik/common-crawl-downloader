from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Data(Base):
    __tablename__ = 'data'

    DOWNLOAD_PENDING = 0
    DOWNLOAD_DOWNLOADING = 1
    DOWNLOAD_FINISHED = 2
    DOWNLOAD_FAILED = 3

    id = Column(Integer, primary_key=True, autoincrement=True)
    uri = Column(String(256), nullable=False)
    size = Column(Integer, nullable=False, default=0)
    date = Column(DateTime)
    process_state = Column(SmallInteger, nullable=False, default=0)
    download_state = Column(SmallInteger, nullable=False, default=0)
    server = Column(Integer, ForeignKey('server.id'))
    server_obj = relationship('Server', back_populates='data_objs')
    process_obj = relationship('Process', uselist=False, back_populates='data_obj')
    year_month = Column(String(30))


class Process(Base):
    __tablename__ = 'process'

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Integer, ForeignKey('data.id'), nullable=False)
    data_obj = relationship('Data', back_populates='process_obj')
    size = Column(Integer, nullable=False, default=0)
    date = Column(DateTime)
    server = Column(Integer, ForeignKey('server.id'))
    server_obj = relationship('Server', back_populates='process_objs')
    uri = Column(String(256))


class Server(Base):
    __tablename__ = 'server'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(15), nullable=False)
    data_objs = relationship('Data', back_populates='server_obj')
    process_objs = relationship('Process', back_populates='server_obj')

    def __repr__(self) -> str:
        return f'Server: id={self.id}, ip={self.ip}'
