import os
import db
import sys
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
from sqlalchemy.engine import URL
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


def format_db_url(url: URL) -> str:
    return f'{url.drivername}://{url.username}@{url.host}:{url.port}/{url.database}'


def update_job_state(session: Session, job: models.Data, state: int):
    job.download_state = state
    session.add(job)
    session.commit()


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
    while True:
        check_connectivity()
        logging.info('Fetching an unclaimed job...')
        try:
            db_engine = db.db_connect(db.db)
            session = Session(bind=db_engine)
            job: models.Data = session \
                .query(models.Data) \
                .filter_by(download_state=models.Data.DOWNLOAD_PENDING) \
                .with_for_update() \
                .first()
            logging.info(f'Database connected: {format_db_url(db_engine.url)}')
        except Exception as e:
            logging.critical(f'Failed to connect to the database: {e}')
            return

        if job is None:
            logging.info('No unclaimed job found. The program is about to exit.')
            session.close()
            return
        update_job_state(session, job, models.Data.DOWNLOAD_DOWNLOADING)
        logging.info(f'A new job is claimed: {{id={job.id}, uri={job.uri}}}.')

        url = f'{url_base}/{job.uri}'
        logging.info(f'Start downloading from URL: {url}.')
        tries = 0
        finished = False
        try:
            file = pathlib.Path(file_base).joinpath(job.uri)
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
                        logging.error(f'An error occurred: {e}')
                        logging.info(f'Retry after {retry_interval} seconds ({retries - tries}) left).')
                        time.sleep(retry_interval)
                        tries += 1
                    else:
                        break
            if finished:
                logging.info('Download succeeded.')
                logging.info(f'The downloaded file is saved at {file}.')
                server = get_server(session, ip)
                job.server_obj = server
                job.date = datetime.datetime.now()
                job.size = int(urlopen(url).info().get('Content-Length', -1))
                update_job_state(session, job, models.Data.DOWNLOAD_FINISHED)
            else:
                logging.error(f'Job {{id={job.id}, uri={job.uri}}} failed.')
                update_job_state(session, job, models.Data.DOWNLOAD_FAILED)
            session.close()
        except KeyboardInterrupt:
            logging.error(f'Job {{id={job.id}, uri={job.uri}}} cancelled.')
            update_job_state(session, job, models.Data.DOWNLOAD_PENDING)
            session.close()
            return


if __name__ == '__main__':
    if len(sys.argv) == 2 or sys.argv[2] != 'console':
        sys.stdout = open(f'log-{sys.argv[1]}.log', 'a')
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(asctime)s [%(levelname)s]] %(message)s')
    socket.setdefaulttimeout(socket_timeout)
    main()
