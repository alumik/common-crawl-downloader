import pathlib
import configparser

CONFIG_PATH = 'configs'
DEFAULT_CONFIG = 'default.conf'


def config() -> configparser.ConfigParser:
    config_parser = configparser.ConfigParser()
    config_path = pathlib.Path(CONFIG_PATH)
    default_config = config_path.joinpath(DEFAULT_CONFIG)
    config_list = [default_config]
    for file in pathlib.Path(config_path).iterdir():
        if file.suffix == '.conf' and file.name != default_config.name:
            config_list.append(file)
    config_parser.read(config_list)
    return config_parser
