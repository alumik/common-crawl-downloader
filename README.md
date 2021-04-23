# Common Crawl Downloader

Languages: [English](https://github.com/AlumiK/common-crawl-downloader/blob/main/README.md) | [中文](https://github.com/AlumiK/common-crawl-downloader/blob/main/README_CN.md)

![python-3.7-3.8-3.9](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue)
[![license-MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/AlumiK/common-crawl-downloader/blob/main/LICENSE)

Distributed download scripts for Common Crawl data.

## Dependencies

Python >= 3.7 is required.

Install dependencies by:

```
pip install -r requirements.txt
```

Please note that `libmysqlclient-dev` or an equivalent one is required on Linux distros：

```
sudo apt install libmysqlclient-dev
```

## Run

### Configurations

The default config file is located at `configs/default.conf`, which lists all the modifiable entries. Their descriptions and default values are listed below:

```ini
[database]
drivername = mysql
username = user
password = password
host = localhost
port = 3306
database = common_crawl

[worker]
; The name of this worker
name = unknown
; The interval of retries in seconds
retry_interval = 5
; The number of retries before giving up
retries = 10
; The timeout of internet connections in seconds
socket_timeout = 30
; The download root path
download_path = downloaded

[schedule]
; Whether to restrict download time
enabled = false
; The start of the allowed download time
start_time = 20:00:00
; The end of the allowed download time
end_time = 07:59:59
; The interval of retries when download is restricted
retry_interval = 300
```

Please **do not** modify the default config file directly. You can create your `local.conf` under the `configs` folder and add the entries you want to modify in it.

An example of a valid local config file:

```ini
[database]
username = common_crawl
password = &WcKLEsX!
host = 10.10.1.217

[schedule]
enabled = true
start_time = 20:00:00
end_time = 07:59:59
```

### Execute the download script

Run the following command at the root path of the project:

```
python src/main.py
```

## Database Structure

### data

| Field | Type | Description |
| :- | :- | :- |
| id | int | **Primary Key** Data ID |
| uri | varchar(256) | The URI of the data, which constitutes the download URL and the folder structure |
| size | int | The size of the data in bytes |
| started_at | datetime | Download start time (CST) |
| finished_at | datetime | Download end time (CST) |
| download_state | tinyint | Download state <br/>`0` for pending<br/>`1` for downloading<br/>`2` for finished<br/>`3` for failed |
| id_worker | int | **Foreign Key** The ID of the worker that downloads this data |
| archive | varchar(30) | The year and month of the data on Common Crawl |

URIs can be obtained from `wet.paths` files on Common Crawl website.

An example of a URI:

```
crawl-data/CC-MAIN-2021-10/segments/1614178347293.1/wet/CC-MAIN-20210224165708-20210224195708-00000.warc.wet.gz
```

### worker

| Field | Type | Description |
| :- | :- | :- |
| id | int | **Primary Key** Worker ID |
| name | varchar(128) | The name of the worker |
