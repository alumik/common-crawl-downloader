import pathlib
import configparser


def config(path: str, default_config: str = 'default.conf') -> configparser.ConfigParser:
    config_parser = configparser.ConfigParser()
    config_path = pathlib.Path(path)
    default_config = config_path.joinpath(default_config)
    config_list = [default_config]
    for file in pathlib.Path(config_path).iterdir():
        if file.suffix == '.conf' and file.name != default_config.name:
            config_list.append(file)
    config_parser.read(config_list)
    return config_parser
