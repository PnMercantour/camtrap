create schema camtrap;
drop table camtrap.project cascade;
create table camtrap.project(
    id int primary key generated always as identity,
    name text unique,
    creation_date timestamp with time zone,
    update_date timestamp with time zone
);
drop table camtrap.file cascade;
create table camtrap.file(
    id int primary key generated always as identity,
    path text,
    parent_id int references camtrap.file(id),
    level int2,
    project_id int references camtrap.project(id),
    creation_date timestamp with time zone,
    update_date timestamp with time zone,
    unique(project_id, path)
);
drop table camtrap.site cascade;
create table camtrap.site(
    id int primary key references camtrap.file(id),
    name text,
    geom geometry(point, 2154),
    project_id int references camtrap.project(id)
);
drop table camtrap.device cascade;
create table camtrap.device(
    id int primary key generated always as identity,
    name text,
    model text
);
drop table camtrap.field_sensor cascade;
create table camtrap.field_sensor(
    id int primary key references camtrap.file(id),
    device_id int references camtrap.device(id),
    site_id int references camtrap.site(id),
    path text,
    geom geometry(point, 2154),
    install_date timestamp without time zone,
    uninstall_date timestamp without time zone
);
drop table camtrap.visit cascade;
create table camtrap.visit(
    id int primary key references camtrap.file(id),
    field_sensor_id int references camtrap.field_sensor(id),
    project_id int references camtrap.project(id),
    install boolean,
    uninstall boolean,
    comment text,
    "time" timestamp without time zone,
    creation_date timestamp with time zone,
    update_date timestamp with time zone
);
drop table camtrap.media cascade;
create table camtrap.media (
    id int primary key references camtrap.file(id),
    visit_id int references camtrap.visit(id),
    field_sensor_id int references camtrap.field_sensor(id),
    project_id int references camtrap.project(id),
    file_type text,
    mime_type text,
    start_time timestamp without time zone,
    duration numeric,
    creation_date timestamp with time zone,
    update_date timestamp with time zone
);