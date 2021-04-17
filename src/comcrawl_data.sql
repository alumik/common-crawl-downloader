create table server
(
	id int auto_increment
		primary key,
	ip varchar(15) not null
);

create table data
(
	id int auto_increment
		primary key,
	uri varchar(256) charset utf8 not null,
	size int default 0 not null,
	date datetime null,
	process_state tinyint(11) default 0 not null comment '0 Not processed
1 Processing
2 Processed',
	download_state tinyint(11) default 0 not null comment '0 Waiting for download
1 Downloading
2 Downloaded
3 Failed',
	server int null,
	`year_month` varchar(30) charset utf8 null,
	constraint data_uri_uindex
		unique (uri),
	constraint data_server_id_fk
		foreign key (server) references server (id)
);

create table process
(
	id int auto_increment
		primary key,
	data int not null,
	size int default 0 not null,
	date datetime null,
	server int null,
	uri varchar(256) null,
	constraint process_data_uindex
		unique (data),
	constraint process_uri_uindex
		unique (uri),
	constraint process_data_id_fk
		foreign key (data) references data (id),
	constraint process_server_id_fk
		foreign key (server) references server (id)
);
