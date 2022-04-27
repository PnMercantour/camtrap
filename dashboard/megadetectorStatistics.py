from pathlib import Path

from megadetector import filter
from metadata import listSites, listVisits, getVisitMetadata

medias = 0
eligible_medias = 0
for site in listSites():
    for visit in listVisits(site):
        md = getVisitMetadata(visit, site)
        filtered = filter(md, {'in_threshold': 0.96, 'include': [
            '1'], 'out_threshold': 0.8, 'exclude': ['2', '3']}, visit, site)
        medias += len(md)
        eligible_medias += len(filtered)

print(medias, 'medias')
print(eligible_medias, 'eligible medias')
