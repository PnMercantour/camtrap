-- Post import script for LWA
--  <level> <type>
-- 1 LWA
-- 2 site
-- 3 field_sensor
-- 4 visit (isodate<sp>sensor_code)
-- 5 media
--
--
--
insert into camtrap.site(id, project_id,name)
select file.id,
    project.id project_id,
    file.name name
from camtrap.file
    join camtrap.project on file.project_id = project.id
where project.name = 'LWA'
    and file.level = 2 on conflict do nothing;
--
--
insert into camtrap.field_sensor(id, project_id, name, site_id)
select file.id id,
    project.id project_id,
    lower(file.name) name,
    file.parent_id site_id
from camtrap.file
    join camtrap.project on file.project_id = project.id
where project.name = 'LWA'
    and file.level = 3 on conflict do nothing;
--
--
insert into camtrap.visit (id, project_id, "date", field_sensor_id, site_id)
select file.id id,
    file.project_id project_id,
    split_part(file.name, ' ', 1)::date date,
    field_sensor.id field_sensor_id,
    field_sensor.site_id site_id
from camtrap.file
    join camtrap.project on file.project_id = project.id
    join camtrap.field_sensor on file.parent_id = field_sensor.id
where file.level = 4
    and project.name = 'LWA' on conflict do nothing;
--
--
update camtrap.media
set visit_id = visit.id,
    field_sensor_id = visit.field_sensor_id
from camtrap.file,
    camtrap.visit,
    camtrap.project
where project.name = 'LWA'
    and file.project_id = project.id
    and media.id = file.id
    and file.parent_id = visit.id;