-- post import script for EPHE project
-- <level> <type>
-- 1 site
-- 1 field_sensor
-- 2 visit (isodate)
-- 3 media
--
--
insert into camtrap.site(id, project_id, name)
select file.id,
    project.id project_id,
    file.name name
from camtrap.file
    join camtrap.project on file.project_id = project.id
where project.name = 'EPHE'
    and file.level = 1 on conflict do nothing;
--
--
insert into camtrap.field_sensor(id, project_id, name, site_id)
select file.id id,
    project.id project_id,
    file.name name,
    file.id site_id
from camtrap.file
    join camtrap.project on file.project_id = project.id
where project.name = 'EPHE'
    and file.level = 1 on conflict do nothing;
--
insert into camtrap.visit (id, project_id, "date",field_sensor_id, site_id) 
select file.id id,
    file.project_id,
    file.name::date,
    field_sensor.id field_sensor_id,
    field_sensor.site_id site_id
from camtrap.file
    join camtrap.project on file.project_id = project.id
    join camtrap.field_sensor on file.parent_id = field_sensor.id
where file.level = 2
    and project.name = 'EPHE' on conflict do nothing;
--
--
update camtrap.media
set visit_id = visit.id,
    field_sensor_id = visit.field_sensor_id
from camtrap.file,
    camtrap.visit,
    camtrap.project
where project.name = 'EPHE'
    and media.project_id = project.id
    and media.id = file.id
    and file.parent_id = visit.id;
--
--