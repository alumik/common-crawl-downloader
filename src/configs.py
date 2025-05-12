import yaml
import dacite
import pathlib
import deepmerge
import dataclasses


@dataclasses.dataclass
class DatabaseConfig:
    drivername: str
    username: str
    password: str
    host: str
    port: int
    database: str


@dataclasses.dataclass
class WorkerConfig:
    name: str
    download_path: str
    max_retries: int
    retry_interval: float


@dataclasses.dataclass
class SchedulerConfig:
    enabled: bool
    start_time: str
    end_time: str
    retry_interval: float


@dataclasses.dataclass
class NetworkConfig:
    connectivity_check_url: str
    timeout: float
    max_retries: int
    retry_interval: float


@dataclasses.dataclass
class Config:
    base_url: str
    timezone: str
    database: DatabaseConfig
    worker: WorkerConfig
    scheduler: SchedulerConfig
    network: NetworkConfig


def load_config(path: str) -> Config:
    path = pathlib.Path(path)
    config_files = sorted(path.rglob('*.yaml'))
    with pathlib.Path(path / 'default.yaml').open() as f:
        config_dict = yaml.safe_load(f)
    for config_file in config_files:
        if config_file.name == 'default.yaml':
            continue
        with config_file.open() as f:
            deepmerge.always_merger.merge(config_dict, yaml.safe_load(f))
    config = dacite.from_dict(Config, config_dict)
    return config
