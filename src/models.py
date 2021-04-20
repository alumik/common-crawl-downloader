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
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    process_state = Column(SmallInteger, nullable=False, default=0)
    download_state = Column(SmallInteger, nullable=False, default=0)
    id_worker = Column(Integer, ForeignKey('worker.id'))
    archive = Column(String(30))

    worker = relationship('Worker', back_populates='data')
    process = relationship('Process', uselist=False, back_populates='data')


class Process(Base):
    __tablename__ = 'process'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_data = Column(Integer, ForeignKey('data.id'), nullable=False)
    size = Column(Integer, nullable=False, default=0)
    processed_at = Column(DateTime)
    id_worker = Column(Integer, ForeignKey('worker.id'))
    uri = Column(String(256))

    data = relationship('Data', back_populates='process')
    worker = relationship('Worker', back_populates='process')


class Worker(Base):
    __tablename__ = 'worker'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)

    data = relationship('Data', back_populates='worker')
    process = relationship('Process', back_populates='worker')
