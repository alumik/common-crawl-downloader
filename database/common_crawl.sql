create table worker
(
    id   int auto_increment
        primary key,
    name varchar(128) not null
);

create table data
(
    id             int auto_increment
        primary key,
    uri            varchar(256) charset utf8 not null,
    size           int         default 0     not null,
    started_at     datetime                  null,
    finished_at    datetime                  null,
    process_state  tinyint(11) default 0     not null comment '0 Not processed
1 Processing
2 Processed',
    download_state tinyint(11) default 0     not null comment '0 Waiting for download
1 Downloading
2 Downloaded
3 Failed',
    id_worker      int                       null,
    archive        varchar(30) charset utf8  null,
    constraint data_uri_uindex
        unique (uri),
    constraint data_worker_id_fk
        foreign key (id_worker) references worker (id)
);

create table process
(
    id           int auto_increment
        primary key,
    id_data      int           not null,
    size         int default 0 not null,
    processed_at datetime      null,
    id_worker    int           null,
    uri          varchar(256)  null,
    constraint process_data_uindex
        unique (id_data),
    constraint process_uri_uindex
        unique (uri),
    constraint process_data_id_fk
        foreign key (id_data) references data (id),
    constraint process_worker_id_fk
        foreign key (id_worker) references worker (id)
);
