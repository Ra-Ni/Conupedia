import re


def process_href(src: str, dst: str = None):
    with open(src, 'r') as fstream:
        content = fstream.read()

    content = re.sub(r'"\.\./([^ ]*)"', r""" " {{ url_for('web', path='\1') }} " """, content)

    if not dst:
        dst = src

    with open(dst, 'w') as fstream:
        fstream.write(content)


if __name__ == '__main__':
    dir = '../web/'
    files = ['student/dashboard.html']
    for file in files:
        path = dir + file
        process_href(path)