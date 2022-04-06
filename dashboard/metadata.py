from pathlib import Path
import json
from config import data_root
from datetime import date, datetime
from functools import lru_cache

exiftoolDateFormat = '%Y:%m:%d %H:%M:%S'


def listSites():
    l = []
    for site in (data_root / 'metadata' / 'sites').iterdir():
        try:
            l.append(int(site.name))
        except:
            print(f'warning:listSites:invalid site id: {site}: ignored')
    l.sort()
    return l


def listVisits(site_id):
    " Sorted list of visit dates for given site id, most recent first"
    l = []
    for visit in (data_root/'metadata'/'sites'/str(site_id)).iterdir():
        try:
            date.fromisoformat(visit.stem)
            l.append(visit.stem)
        except:
            print(f'warning:listVisits:invalid visit header: {visit}: ignored')
    l.sort(reverse=True)
    return l


def getVisitMetadata(visit, site_id):
    path = (data_root / 'metadata' / 'sites' /
            str(site_id) / visit).with_suffix('.json')
    if (not path.exists()):
        return buildMetadata(visit, site_id)
    with path.open('r') as f:
        md = json.load(f)
        return md


@lru_cache(maxsize=64)
def getVisitMetadataFromCache(visit, site_id):
    return getVisitMetadata(visit, site_id)


def buildMetadata(visit, site_id):
    exif_path = data_root / 'exif' / ('Maille ' + str(site_id)) / visit
    if not exif_path.exists():
        print(f'buildMetadata: {exif_path} does not exist')
        return
    l = []
    for p in exif_path.iterdir():
        if p.suffix != '.json':
            continue
        with p.open('r') as f:
            md = json.load(f)[0]
            if md.get('ExifTool:Error') is not None:
                print(p, 'ignored:', md['ExifTool:Error'])
                continue
            record = dict(
                fileName=md['File:FileName'],
                fileType=md['File:FileType'],
                path=md["SourceFile"],
            )
            if record["fileType"] == "MP4":
                record["startTime"] = (datetime.strptime(
                    md["QuickTime:MediaCreateDate"], exiftoolDateFormat)).isoformat()
                record["duration"] = md["QuickTime:TrackDuration"]
            elif record["fileType"] == 'JPEG':
                record["startTime"] = (datetime.strptime(
                    md["EXIF:DateTimeOriginal"], exiftoolDateFormat)).isoformat()
                record["duration"] = 0
            else:
                print(p, 'ignored: unhandled filetype', record["fileType"])
            l.append(record)

    l.sort(key=lambda media: media['startTime'])
    dest_dir = data_root / 'metadata' / 'sites' / str(site_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with (dest_dir / visit).with_suffix('.json').open('w') as f:
        json.dump(l, f)
    return l


if __name__ == '__main__':
    for site in (data_root / 'exif').iterdir():
        split = site.name.split(' ')
        if split[0] == 'Maille':
            site_id = int(split[1])
            for visit in site.iterdir():
                try:
                    date.fromisoformat(visit.name)
                    buildMetadata(visit.name, site_id)
                except:
                    print(f'warning:invalid repository: {visit}: ignored')
