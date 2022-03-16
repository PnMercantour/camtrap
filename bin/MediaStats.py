from pathlib import Path
from datetime import date

root = Path('/media/vprunet/INTENSO1')


def parseSite(name):
    "returns site_id (an int) or None"
    tokens = name.split(' ')
    if len(tokens) == 2 and tokens[0] == 'Maille':
        try:
            return int(tokens[1])
        except:
            return None
    return None


def parseVisit(name):
    "returns visit (a iso date string) or None"
    try:
        date.fromisoformat(name)
        return name
    except:
        return None


def visitInfo():
    for p in root.iterdir():
        site_id = parseSite(p.name)
        if site_id is not None:
            if p.is_dir():
                for v in p.iterdir():
                    visit = parseVisit(v.name)
                    if visit is not None:
                        if v.is_dir():
                            print(v, sum(1 for f in v.glob('*.MP4')))
                        else:
                            print('Visite: Pas un répertoire:', v)
                    else:
                        print('Visite: Format non reconnu', v)
            else:
                print('Site: Pas un répertoire:', p)
        else:
            print('Site: Format non reconnu:', p)


visitInfo()
