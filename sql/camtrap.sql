create schema camtrap;
drop table camtrap.project cascade;
create table camtrap.project(
    id int primary key generated always as identity,
    name text unique,
    meta_creation_date timestamp with time zone,
    meta_update_date timestamp with time zone
);
--
--
drop table camtrap.file cascade;
create table camtrap.file(
    id int primary key generated always as identity,
    project_id int references camtrap.project(id) on delete
    set null,
        name text,
        path text,
        parent_id int references camtrap.file(id),
        level int2,
        meta_creation_date timestamp with time zone,
        meta_update_date timestamp with time zone,
        unique(project_id, path)
);
--
--
drop table camtrap.site cascade;
create table camtrap.site(
    id int primary key references camtrap.file(id) on delete cascade,
    project_id int references camtrap.project(id) on delete cascade,
    name text,
    geom geometry(point, 2154)
);
--
--
drop table camtrap.sensor cascade;
create table camtrap.sensor(
    id int primary key generated always as identity,
    name text,
    model text
);
--
--
drop table camtrap.field_sensor cascade;
create table camtrap.field_sensor(
    id int primary key references camtrap.file(id) on delete cascade,
    project_id int references camtrap.project(id) on delete cascade,
    name text,
    sensor_id int references camtrap.sensor(id) on delete
    set null,
        site_id int references camtrap.site(id) on delete
    set null,
        geom geometry(point, 2154)
);
--
--
drop table camtrap.visit cascade;
create table camtrap.visit(
    id int primary key references camtrap.file(id) on delete cascade,
    project_id int references camtrap.project(id) on delete cascade,
    "date" date,
    info text,
    field_sensor_id int references camtrap.field_sensor(id) on delete
    set null,
        site_id int references camtrap.site(id) on delete
    set null
);
--
--
drop table camtrap.media cascade;
create table camtrap.media (
    id int primary key references camtrap.file(id) on delete cascade,
    project_id int references camtrap.project(id) on delete cascade,
    visit_id int references camtrap.visit(id) on delete
    set null,
        field_sensor_id int references camtrap.field_sensor(id) on delete
    set null,
        file_type text,
        mime_type text,
        start_time timestamp without time zone,
        duration numeric,
        meta_creation_date timestamp with time zone,
        meta_update_date timestamp with time zone
);