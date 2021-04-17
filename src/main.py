import os
import db
import wget
import time
import models
import socket
import logging
import pathlib
import datetime
import progbar as pb

from urllib.request import urlopen
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

url_base = 'https://commoncrawl.s3.amazonaws.com'
retry_interval = 5
retries = 10
socket_timeout = 30
if os.name == 'nt':
    file_base = 'downloaded'
else:
    file_base = '/home/common_crawl_data'


def check_connectivity():
    try:
        urlopen("https://www.baidu.com", timeout=10)
    except Exception as e:
        logging.critical(f'Connectivity check failed: {e}')
        exit(-1)


def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((db.db.get('host'), db.db.get('port')))
    ip = s.getsockname()[0]
    s.close()
    return ip


def get_server(session: Session, ip: str) -> models.Server:
    try:
        server = session.query(models.Server).filter_by(ip=ip).one()
    except NoResultFound:
        server = models.Server()
        server.ip = ip
        session.add(server)
        session.commit()
    return server


def main():
    ip = get_ip()
    db_engine = db.db_connect(db.db)

    while True:
        check_connectivity()

        logging.info('Fetching an unclaimed job...')
        try:
            session = Session(bind=db_engine)
            job: models.Data = session \
                .query(models.Data) \
                .filter_by(download_state=models.Data.DOWNLOAD_PENDING) \
                .with_for_update() \
                .first()
        except Exception as e:
            logging.critical(f'Failed to connect to the database: {e}')
            return

        if job is None:
            logging.info('No unclaimed job found. The program is about to exit.')
            session.close()
            return

        uri = job.uri
        job.download_state = models.Data.DOWNLOAD_DOWNLOADING
        session.add(job)
        session.commit()
        session.close()
        logging.info(f'A new job is claimed: {{id={job.id}, uri={job.uri}}}.')

        url = f'{url_base}/{uri}'
        logging.info(f'Downloading from {url}')
        tries = 0
        finished = False
        try:
            file = pathlib.Path(file_base).joinpath(uri)
            file.parent.mkdir(parents=True, exist_ok=True)

            while True:
                try:
                    progbar = pb.DownloadProgBar()
                    wget.download(url, out=str(file), bar=progbar.update)
                    finished = True
                    break
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    if tries < retries:
                        logging.error(f'An error has occurred: {e}')
                        logging.info(f'Retry after {retry_interval} seconds ({retries - tries} left)).')
                        time.sleep(retry_interval)
                        tries += 1
                    else:
                        break

            session = Session(bind=db_engine)
            job: models.Data = session \
                .query(models.Data) \
                .filter_by(uri=uri) \
                .with_for_update() \
                .one()
            if finished:
                logging.info(f'Job {{id={job.id}, uri={job.uri}}} succeeded.')
                logging.info(f'The downloaded file is saved at {file}.')
                job.server_obj = get_server(session, ip)
                job.date = datetime.datetime.now()
                job.size = int(urlopen(url).info().get('Content-Length', -1))
                job.state = models.Data.DOWNLOAD_FINISHED
            else:
                logging.error(f'Job {{id={job.id}, uri={job.uri}}} failed.')
                job.state = models.Data.DOWNLOAD_FAILED
            session.add(job)
            session.commit()
            session.close()

        except KeyboardInterrupt:
            session = Session(bind=db_engine)
            job: models.Data = session \
                .query(models.Data) \
                .filter_by(uri=uri) \
                .with_for_update() \
                .one()
            logging.warning(f'Job {{id={job.id}, uri={job.uri}}} cancelled.')
            job.state = models.Data.DOWNLOAD_PENDING
            session.add(job)
            session.commit()
            session.close()
            return


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s [%(levelname)s]] %(message)s')
    socket.setdefaulttimeout(socket_timeout)
    main()
