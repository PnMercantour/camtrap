from pathlib import Path
import json
from config import data_root
from datetime import date, datetime
from metadata import listSites, listVisits
from megadetectorData import getVisitData


def processVisit(visit, site_id):
    nok = 0
    ok = 0
    for (name, report) in getVisitData(visit, site_id).items():
        if report['max_detection_conf'] < 0.5:
            nok += 1
        else:
            ok += 1
    print(site_id, visit, ok, nok)
    return (ok, nok)


if __name__ == '__main__':
    ok_count = 0
    nok_count = 0
    for site_id in listSites():
        print('site', site_id)
        for visit in listVisits(site_id):
            (ok, nok) = processVisit(visit, site_id)
            ok_count += ok
            nok_count += nok
    print('Done!')
    print(ok_count, nok_count)
