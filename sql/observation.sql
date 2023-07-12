create table camtrap.observation_type(
    id smallint primary key generated always as identity,
    application text unique not null,
    version smallint
);
create table camtrap.observation(
    id int primary key generated always as identity,
    project_id int references camtrap.project(id) on delete cascade,
    digitizer text,
    digit_timestamp timestamp with time zone default now(),
    observation_type_id smallint references camtrap.observation_type(id),
    payload json
);
create table camtrap.obsmedia(
    id int primary key generated always as identity,
    observation_id int not null references camtrap.observation(id) on delete cascade,
    media_id int not null references camtrap.media(id) on delete cascade,
    ref json
);