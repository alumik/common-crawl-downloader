import os
import db
import sys
import wget
import time
import pytz
import models
import socket
import logging
import pathlib
import datetime
import progbar as pb

from urllib.request import urlopen
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from colorama import Fore, Back

connectivity_check_url = 'https://www.baidu.com'
url_base = 'https://commoncrawl.s3.amazonaws.com'
retry_interval = 5
retries = 10
socket_timeout = 30
timezone = 'Asia/Shanghai'
if os.name == 'nt':
    file_base = 'downloaded'
else:
    file_base = '/home/common_crawl_data'


def panic(message: str):
    logging.critical(message)
    sys.exit(-1)


def check_connectivity():
    tries = 0
    while True:
        try:
            urlopen(connectivity_check_url, timeout=30)
        except Exception as e:
            if tries < retries:
                logging.error(f'{Fore.LIGHTRED_EX}Connectivity check failed: {e}{Fore.RESET}')
                logging.info(f'Retry after {retry_interval} seconds ({retries - tries} left)).')
                time.sleep(retry_interval)
                tries += 1
            else:
                panic(f'{Fore.RED}Connectivity check failed after {retries} retries.{Fore.RESET}')
            continue
        break


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
        uri = None
        tries = 0
        while True:
            try:
                session.begin()
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
                logging.info(f'New job fetched: {Fore.CYAN}{{id={job.id}, uri={job.uri}}}{Fore.RESET}.')
                session.close()
            except Exception as e:
                if tries < retries:
                    session.rollback()
                    logging.error(f'{Fore.LIGHTRED_EX}An error has occurred: {e}{Fore.RESET}')
                    logging.info(f'Retry after {retry_interval} seconds ({retries - tries} left)).')
                    time.sleep(retry_interval)
                    tries += 1
                else:
                    panic(f'{Fore.RED}Failed to fetch a new job after {retries} retries.{Fore.RESET}')
                continue
            break

        url = f'{url_base}/{uri}'
        logging.info(f'Downloading from {Fore.CYAN}{url}{Fore.RESET}')
        session = Session(bind=db_engine)

        try:
            file = pathlib.Path(file_base).joinpath(uri)
            file.parent.mkdir(parents=True, exist_ok=True)

            tries = 0
            while True:
                try:
                    progbar = pb.DownloadProgBar()
                    wget.download(url, out=str(file), bar=progbar.update)
                    job = find_job_by_uri(session=session, uri=uri)
                    job.server_obj = find_server_by_ip(session=session, ip=ip)
                    job.date = datetime.datetime.now(tz=pytz.timezone(timezone))
                    job.size = int(urlopen(url).info().get('Content-Length', -1))
                    job.download_state = models.Data.DOWNLOAD_FINISHED
                    logging.info(f'Job {Back.GREEN}succeeded{Back.RESET}: '
                                 f'{Fore.CYAN}{{id={job.id}, uri={job.uri}}}{Fore.RESET}.')
                    break
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    if tries < retries:
                        logging.error(f'{Fore.LIGHTRED_EX}An error has occurred: {e}{Fore.RESET}')
                        logging.info(f'Retry after {retry_interval} seconds ({retries - tries} left)).')
                        time.sleep(retry_interval)
                        tries += 1
                    else:
                        job = find_job_by_uri(session=session, uri=uri)
                        job.download_state = models.Data.DOWNLOAD_FAILED
                        logging.error(f'Job {Back.RED}failed{Back.RESET}: '
                                      f'{Fore.CYAN}{{id={job.id}, uri={job.uri}}}{Fore.RESET}.')
                        break

            session.add(job)
            session.commit()
            session.close()

        except KeyboardInterrupt:
            job = find_job_by_uri(session=session, uri=uri)
            job.download_state = models.Data.DOWNLOAD_PENDING
            logging.warning(f'Job {Back.YELLOW}{Fore.BLACK}cancelled{Fore.RESET}{Back.RESET}: '
                            f'{Fore.CYAN}{{id={job.id}, uri={job.uri}}}{Fore.RESET}.')
            session.add(job)
            session.commit()
            session.close()
            return


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)8s] %(message)s')
    socket.setdefaulttimeout(socket_timeout)
    main()
