import sys
import wget
import time
import pytz
import socket
import logging
import pathlib
import colorama
import datetime
import requests
import argparse

from urllib.request import urlopen
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

import db
import utils
import models
import configs

from src.models import Data


def panic(message: str):
    logging.critical(message)
    sys.exit(-1)


def check_connectivity(config: configs.Config):
    retries = 0
    connectivity_check_url = config.network.connectivity_check_url
    timeout = config.network.timeout
    max_retries = config.network.max_retries
    retry_interval = config.network.retry_interval
    while True:
        try:
            requests.head(connectivity_check_url, timeout=timeout)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if retries < max_retries:
                logging.error(
                    f'{colorama.Fore.LIGHTRED_EX}'
                    f'Connectivity check failed: {e}'
                    f'{colorama.Fore.RESET}'
                )
                logging.info(f'Retry after {retry_interval} seconds ({max_retries - retries} left).')
                time.sleep(retry_interval)
                retries += 1
            else:
                panic(
                    f'{colorama.Fore.LIGHTRED_EX}'
                    f'Connectivity check failed after {max_retries} retries.'
                    f'{colorama.Fore.RESET}'
                )
            continue
        break


def check_schedule(config: configs.Config):
    enabled = config.scheduler.enabled
    start_time = config.scheduler.start_time
    end_time = config.scheduler.end_time
    retry_interval = config.scheduler.retry_interval
    if not enabled:
        return
    logging.info(
        f'Download schedule: '
        f'{colorama.Fore.LIGHTMAGENTA_EX}'
        f'{{start_time={start_time}, end_time={end_time}}}'
        f'{colorama.Fore.RESET}'
        f'.'
    )
    while True:
        now = datetime.datetime.now(tz=pytz.timezone(config.timezone)).strftime('%H:%M:%S')
        if (start_time <= end_time and (now < start_time or now > end_time)) or \
                (start_time > end_time and (end_time < now < start_time)):
            time.sleep(retry_interval)
        else:
            break


def find_or_create_worker_by_name(session: Session, name: str) -> models.Worker:
    try:
        worker = session.query(models.Worker).filter_by(name=name).one()
    except NoResultFound:
        worker = models.Worker()
        worker.name = name
        session.add(worker)
        session.commit()
    return worker


def find_job_by_uri(session: Session, uri: str) -> Data:
    return session \
        .query(models.Data) \
        .filter_by(uri=uri) \
        .one()


def get_args():
    parser = argparse.ArgumentParser(description='distributed download scripts for Common Crawl data')
    parser.add_argument('--config', type=str, default='configs', help='path to the config directory')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    config = configs.load_config(args.config)
    socket.setdefaulttimeout(config.network.timeout)
    db_engine = db.db_connect(config)

    while True:
        try:
            check_schedule(config)
            check_connectivity(config)
        except KeyboardInterrupt:
            logging.info(f'Bye.')
            return

        logging.info('Fetching a new job...')
        session = Session(bind=db_engine)
        uri = None
        retries = 0
        while True:
            try:
                session.begin()
                job: models.Data = session \
                    .query(models.Data) \
                    .with_for_update(of=models.Data, skip_locked=True) \
                    .filter_by(download_state=models.Data.DOWNLOAD_PENDING) \
                    .first()
                if job is None:
                    logging.info('No unclaimed job found. This program is about to exit.')
                    session.close()
                    return
                uri = job.uri
                job.started_at = datetime.datetime.now(tz=pytz.timezone(config.timezone))
                job.download_state = models.Data.DOWNLOAD_DOWNLOADING
                session.add(job)
                session.commit()
                logging.info(
                    f'New job fetched: '
                    f'{colorama.Fore.LIGHTCYAN_EX}'
                    f'{{id={job.id}, uri={job.uri}}}'
                    f'{colorama.Fore.RESET}'
                    f'.'
                )
                session.close()
            except Exception as e:
                if retries < config.worker.max_retries:
                    session.rollback()
                    logging.error(
                        f'{colorama.Fore.LIGHTRED_EX}'
                        f'An error has occurred: {e}'
                        f'{colorama.Fore.RESET}'
                    )
                    logging.info(
                        f'Retry after {config.worker.retry_interval} seconds '
                        f'({config.worker.max_retries - retries} left).'
                    )
                    time.sleep(config.worker.retry_interval)
                    retries += 1
                else:
                    panic(
                        f'{colorama.Fore.LIGHTRED_EX}'
                        f'Failed to fetch a new job after {config.worker.max_retries} retries.'
                        f'{colorama.Fore.RESET}'
                    )
                continue
            break

        url = f'{config.base_url}/{uri}'
        logging.info(
            f'Download from '
            f'{colorama.Fore.LIGHTCYAN_EX}'
            f'{url}'
            f'{colorama.Fore.RESET}'
        )
        session = Session(bind=db_engine)

        try:
            file = pathlib.Path(config.worker.download_path).joinpath(uri)
            file.parent.mkdir(parents=True, exist_ok=True)

            retries = 0
            while True:
                try:
                    progbar = utils.DownloadProgBar()
                    wget.download(url, out=str(file), bar=progbar.update)
                    job = find_job_by_uri(session=session, uri=uri)
                    job.worker = find_or_create_worker_by_name(session=session, name=config.worker.name)
                    job.finished_at = datetime.datetime.now(tz=pytz.timezone(config.timezone))
                    job.size = int(urlopen(url).info().get('Content-Length', -1))
                    job.download_state = models.Data.DOWNLOAD_FINISHED
                    logging.info(
                        f'Job '
                        f'{colorama.Back.GREEN}{colorama.Fore.BLACK}'
                        f'succeeded'
                        f'{colorama.Fore.RESET}{colorama.Back.RESET}'
                        f'.'
                    )
                    break
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    if retries < config.worker.max_retries:
                        logging.error(
                            f'{colorama.Fore.LIGHTRED_EX}'
                            f'An error has occurred: {e}'
                            f'{colorama.Fore.RESET}'
                        )
                        logging.info(
                            f'Retry after {config.worker.retry_interval} seconds '
                            f'({config.worker.max_retries - retries} left).'
                        )
                        time.sleep(config.worker.retry_interval)
                        retries += 1
                    else:
                        job = find_job_by_uri(session=session, uri=uri)
                        job.download_state = models.Data.DOWNLOAD_FAILED
                        logging.error(
                            f'Job '
                            f'{colorama.Back.RED}'
                            f'failed'
                            f'{colorama.Back.RESET}'
                            f'.'
                        )
                        break

            session.add(job)
            session.commit()
            session.close()

        except KeyboardInterrupt:
            job = find_job_by_uri(session=session, uri=uri)
            job.started_at = None
            job.download_state = models.Data.DOWNLOAD_PENDING
            logging.warning(
                f'Job '
                f'{colorama.Back.YELLOW}{colorama.Fore.BLACK}'
                f'cancelled'
                f'{colorama.Fore.RESET}{colorama.Back.RESET}'
                f'.'
            )
            session.add(job)
            session.commit()
            session.close()
            return


if __name__ == '__main__':
    colorama.just_fix_windows_console()
    logging.basicConfig(
        level=logging.INFO,
        format=f'{colorama.Style.BRIGHT}[%(asctime)s] [%(levelname)8s]{colorama.Style.RESET_ALL} %(message)s',
    )
    main()
