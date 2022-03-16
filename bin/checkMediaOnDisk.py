from pathlib import Path
from datetime import date

root = Path('/media/vprunet/INTENSO')


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


def guessVisit(name, site_id):
    "tries to guess the visit from a custom format"
    try:
        tokens = name.split('_')
        if len(tokens) == 2 and tokens[0] == 'Maille'+str(site_id):
            date.fromisoformat(tokens[1])
            return tokens[1]
    except:
        pass
    print('failed to guess visit', name, site_id)
    return None


def fixVisits():
    for p in root.iterdir():
        site_id = parseSite(p.name)
        if site_id is not None:
            if p.is_dir():
                for v in p.iterdir():
                    visit = parseVisit(v.name)
                    if visit is not None:
                        if v.is_dir():
                            pass
                        else:
                            print('Visite: Pas un répertoire:', v)
                    else:
                        print('Visite: Format non reconnu', v)
                        # print('correction automatique')
                        visit = guessVisit(v.name, site_id)
                        # print('guess:', visit)
                        if visit is not None:
                            new_v = v.parent / visit
                            print('fix to ', new_v)
                            if new_v.exists():
                                print(
                                    'correction impossible, le répertoire existe', new_v)
                            else:
                                v.rename(new_v)
            else:
                print('Site: Pas un répertoire:', p)


def visitInfo():
    for p in root.iterdir():
        site_id = parseSite(p.name)
        if site_id is not None:
            if p.is_dir():
                for v in p.iterdir():
                    visit = parseVisit(v.name)
                    if visit is not None:
                        if v.is_dir():
                            pass
                        else:
                            print('Visite: Pas un répertoire:', v)
                    else:
                        print('Visite: Format non reconnu', v)
            else:
                print('Site: Pas un répertoire:', p)
        else:
            print('Site: Format non reconnu:', p)


def mediaInfo():
    for p in root.iterdir():
        site_id = parseSite(p.name)
        if site_id is not None:
            if p.is_dir():
                for v in p.iterdir():
                    visit = parseVisit(v.name)
                    if visit is not None:
                        if v.is_dir():
                            for m in v.iterdir():
                                if m.is_dir():
                                    print('Media: pas un média', m)
                                if m.suffix not in ['.MP4', '.JPG']:
                                    print('Media: format non reconnu', m)
                        else:
                            print('Visite: Pas un répertoire:', v)
                    else:
                        print('Visite: Format non reconnu', v)
            else:
                print('Site: Pas un répertoire:', p)
        else:
            print('Site: Format non reconnu:', p)


mediaInfo()
visitInfo()
# fixVisits()
