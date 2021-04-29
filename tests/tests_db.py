import db
import time
import configs

from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base, Session


class Test(declarative_base()):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer, nullable=False)


config = configs.config('configs')
db_conf = db.get_database_config(config)
db_engine = db.db_connect(db_conf)
session = Session(bind=db_engine)
session.begin()
test: Test = session \
    .query(Test) \
    .with_for_update(skip_locked=True) \
    .filter_by(state=1) \
    .first()
if test is None:
    print('No entry found.')
else:
    print(test.id)
    test.state = 2
    time.sleep(30)
    session.add(test)
    session.commit()
session.close()
