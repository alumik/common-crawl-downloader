# Common Crawl Downloader

![version-1.0.0](https://img.shields.io/badge/version-1.0.0-blue)
![python->=3.9](https://img.shields.io/badge/python->=3.9-blue?logo=python&logoColor=white)
![GitHub License](https://img.shields.io/github/license/alumik/common-crawl-downloader)

Distributed download scripts for Common Crawl data.

## Dependencies

Python >= 3.9 is required.

Install dependencies by:

```
pip install -r requirements.txt
```

## Run

### Configurations

The default config file is located at `configs/default.yaml`, which lists all the modifiable entries. Their descriptions
and default values are listed below:

```yaml
database:
  drivername: mysql+pymysql
  username: user
  password: password
  host: localhost
  port: 3306
  database: common_crawl

worker:
  # The name of the worker, which is used to identify the worker in the database
  name: unknown
  download_path: downloaded
  max_retries: 10
  retry_interval: 5

scheduler:
  # Whether to restrict download time
  enabled: false
  # The start of the allowed download time
  start_time: '20:00:00'
  # The end of the allowed download time
  end_time: '07:59:59'
  retry_interval: 300

network:
  connectivity_check_url: http://www.baidu.com/
  timeout: 30
  max_retries: 10
  retry_interval: 5

timezone: Asia/Shanghai
base_url: https://commoncrawl.s3.amazonaws.com/
```

**Do not** modify the default config file directly. You can create your own `local.yaml` under the `configs` folder and
add modified entries in it.

An example of a valid local config file:

```yaml
database:
  username = common_crawl
  password = &WcKLEsX!
  host = 10.10.1.217

scheduler:
  enabled = true
  start_time = '20:00:00'
  end_time = '07:59:59'
```

### Execute the download script

Run the following command at the root path of the project:

```
python src/main.py
```

**Always** press `CTRL-C` to exit the download process. Killing it directly will cause data loss and inconsistency in
database.

## Database Structure

### data

| Field          | Type         | Description                                                                                         |
|:---------------|:-------------|:----------------------------------------------------------------------------------------------------|
| id             | int          | **Primary Key** Data ID                                                                             |
| uri            | varchar(256) | The URI of the data, which constitutes the download URL and the folder structure                    |
| size           | int          | The size of the data in bytes                                                                       |
| started_at     | datetime     | Download start time (CST)                                                                           |
| finished_at    | datetime     | Download end time (CST)                                                                             |
| download_state | tinyint      | Download state <br/>`0` for pending<br/>`1` for downloading<br/>`2` for finished<br/>`3` for failed |
| id_worker      | int          | **Foreign Key** The ID of the worker that downloads this data                                       |
| archive        | varchar(30)  | The year and month of the data on Common Crawl                                                      |

URIs can be obtained from `wet.paths` files on Common Crawl website.

An example of a URI:

```
crawl-data/CC-MAIN-2021-10/segments/1614178347293.1/wet/CC-MAIN-20210224165708-20210224195708-00000.warc.wet.gz
```

### worker

| Field | Type         | Description               |
|:------|:-------------|:--------------------------|
| id    | int          | **Primary Key** Worker ID |
| name  | varchar(128) | The name of the worker    |
