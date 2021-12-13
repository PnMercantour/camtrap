import visitDigest


def filter(path, id, date, in_threshold=0.96, out_threshold=0.7):
    l = []
    l_control = []
    for (video, report) in visitDigest.readFromCache(path, id, date).items():
        if report.get('1', 0) > in_threshold and max(report.get('2', 0), report.get(3, 0)) < out_threshold:
            l.append(video)
        else:
            l_control.append(video)
        l_control.sort()
        l.sort()
    return l, l_control
