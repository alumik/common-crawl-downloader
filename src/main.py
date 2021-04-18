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

connectivity_check_url = 'https://www.baidu.com'
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
        urlopen(connectivity_check_url, timeout=10)
    except Exception as e:
        logging.critical(f'Internet connectivity check failed: {e}')
        exit(-1)


def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((db.db_conf.get('host'), db.db_conf.get('port')))
    ip = s.getsockname()[0]
    s.close()
    return ip


def find_server_by_ip(session: Session, ip: str) -> models.Server:
    try:
        server = session.query(models.Server).filter_by(ip=ip).one()
    except NoResultFound:
        server = models.Server()
        server.ip = ip
        session.add(server)
        session.commit()
    return server


def find_job_by_uri(session: Session, uri: str) -> models.Data:
    return session \
        .query(models.Data) \
        .filter_by(uri=uri) \
        .one()


def main():
    ip = get_ip()
    db_engine = db.db_connect(db.db_conf)

    while True:
        check_connectivity()

        logging.info('Fetching a new job...')
        session = Session(bind=db_engine)
        while True:
            try:
                job: models.Data = session \
                    .query(models.Data) \
                    .with_for_update() \
                    .filter_by(download_state=models.Data.DOWNLOAD_PENDING) \
                    .first()
                if job is None:
                    logging.info('No unclaimed job found. This program is about to exit.')
                    session.close()
                    return
                uri = job.uri
                job.download_state = models.Data.DOWNLOAD_DOWNLOADING
                session.add(job)
                session.commit()
                logging.info(f'A new job is fetched: {{id={job.id}, uri={job.uri}}}.')
                break
            except Exception as e:
                logging.critical(f'Failed to fetch a new job: {e}')
                session.rollback()
        session.close()

        url = f'{url_base}/{uri}'
        logging.info(f'Downloading from {url}')
        tries = 0
        try:
            file = pathlib.Path(file_base).joinpath(uri)
            file.parent.mkdir(parents=True, exist_ok=True)

            while True:
                try:
                    progbar = pb.DownloadProgBar()
                    wget.download(url, out=str(file), bar=progbar.update)
                    session = Session(bind=db_engine)
                    job = find_job_by_uri(session=session, uri=uri)
                    job.server_obj = find_server_by_ip(session=session, ip=ip)
                    job.date = datetime.datetime.now()
                    job.size = int(urlopen(url).info().get('Content-Length', -1))
                    job.download_state = models.Data.DOWNLOAD_FINISHED
                    logging.info(f'Job succeeded: {{id={job.id}, uri={job.uri}}}.')
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
                        job = find_job_by_uri(session=session, uri=uri)
                        job.download_state = models.Data.DOWNLOAD_FAILED
                        logging.error(f'Job failed: {{id={job.id}, uri={job.uri}}}.')

            session.add(job)
            session.commit()
            session.close()

        except KeyboardInterrupt:
            session = Session(bind=db_engine)
            job = find_job_by_uri(session=session, uri=uri)
            job.download_state = models.Data.DOWNLOAD_PENDING
            logging.warning(f'Job cancelled: {{id={job.id}, uri={job.uri}}}.')
            session.add(job)
            session.commit()
            session.close()
            return


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s [%(levelname)s]] %(message)s')
    socket.setdefaulttimeout(socket_timeout)
    main()
