# Common Crawl 数据下载器

语言: [English](https://github.com/AlumiK/common-crawl-downloader/blob/main/README.md) | [中文](https://github.com/AlumiK/common-crawl-downloader/blob/main/README_CN.md)

![python-3.7-3.8-3.9](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue)
[![license-MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/AlumiK/common-crawl-downloader/blob/main/LICENSE)

Common Crawl 数据分布式下载脚本。

## 环境配置

脚本需要使用 Python >= 3.7 运行。

使用如下命令安装相关依赖：

```
pip install -r requirements.txt
```

注意：如果是在 Ubuntu 系统上部署，可能需要额外安装 `libmysqlclient-dev`：

```
sudo apt install libmysqlclient-dev
```

其他 Linux 发行版请自行安装对应依赖。

## 运行

### 修改配置文件

默认配置文件为 `configs/default.conf`，其中列出了可修改的相关配置。配置说明及默认值如下：

```ini
; 数据库相关配置
[database]
; 数据库类型
drivername = mysql
; 数据库用户名
username = user
; 数据库密码
password = password
; 数据库地址
host = localhost
; 数据库端口
port = 3306
; 数据库名称
database = common_crawl

; 下载器相关配置
[worker]
; 下载器名称，用于在数据库中标识下载设备
name = unknown
; 失败重试间隔（秒）
retry_interval = 5
; 失败重试次数
retries = 10
; 网络连接超时时间（秒）
socket_timeout = 30
; 下载路径
download_path = downloaded

; 限制允许进行下载的时间
[schedule]
; 是否对允许进行下载的时间进行限制
enabled = false
; 允许进行下载的开始时间
start_time = 20:00:00
; 允许进行下载的结束时间
end_time = 07:59:59
; 如果在允许下载的时间段之外，重新查询是否能进行下载的时间间隔（秒）
retry_interval = 300
```

请不要直接修改默认配置文件。如果需要覆盖某些默认配置，可以在`configs` 文件夹下新建一个 `local.conf` 文件，在里面添加需要修改的配置条目。

下面是有效本地配置文件的一个例子：

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

### 启动下载脚本

在项目根目录下运行：

```
python src/main.py
```

## 数据库结构

### data 表

数据对象

| 字段名 | 类型 | 说明 |
| :- | :- | :- |
| id | int | **主键** 数据 ID |
| uri | varchar(256) | 数据唯一标识符，也是下载链接及目录结构 |
| size | int | 数据大小（字节） |
| started_at | datetime | 任务领取时间（CST） |
| finished_at | datetime | 下载完成时间（CST） |
| download_state | tinyint | 下载状态<br/>`0` 代表待下载<br/>`1` 代表下载中<br/>`2` 代表下载成功<br/>`3` 代表下载失败 |
| id_worker | int | **外键** 下载进程 ID |
| archive | varchar(30) | 数据在 Common Crawl 上的年月 |

URI 可以从下载自 Common Crawl 的 `wet.paths` 文件中得到。

URI 示例:

```
crawl-data/CC-MAIN-2021-10/segments/1614178347293.1/wet/CC-MAIN-20210224165708-20210224195708-00000.warc.wet.gz
```

### worker 表

下载进程对象

| 字段名 | 类型 | 说明 |
| :- | :- | :- |
| id | int | **主键** 下载进程 ID |
| name | varchar(128) | 下载进程名称 |
