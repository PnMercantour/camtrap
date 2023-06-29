insert into camtrap.visit (id, project_id, "time") (
        select file.id,
            project_id,
            substring(
                path
                from '..........$'
            )::timestamp without time zone time
        from camtrap.file
            join camtrap.project on file.project_id = project.id
        where level = 2
            and project.name = 'test'
    ) on conflict(id) do
update
set (project_id, "time") = (excluded.project_id, excluded.time);
--
--
update camtrap.media
set visit_id = visit.id
from camtrap.file,
    camtrap.visit
where media.id = file.id
    and file.parent_id = visit.id;
--
    --