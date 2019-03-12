#!/usr/bin/env python3

from pathlib import Path
import json
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError

from threading import Thread
from queue import Queue

q = Queue()


def download():
    while True:
        path, member = q.get()
        link = member['imageURL']
        name = member['name']
        if name == "" or link == "":
            return
        purl = urlparse(link)
        out = path / name
        out.mkdir(exist_ok=True)
        fn = out / Path(purl.path).name.strip()
        try:
            print("[save]", name, str(fn))
            with urlopen(link) as f:
                fn.write_bytes(f.read())
        except HTTPError:
            print("[fail]", link)
        finally:
            q.task_done()


def main():
    for p in [f for f in Path("data/profile").glob("*") if f.is_dir()]:
        with (p / "members.json").open() as f:
            members = json.load(f)
            print(p.name+":", len(members), "profile images")
            for m in members:
                q.put((p, m))
    for _ in range(8):
        t = Thread(target=download)
        t.daemon = True
        t.start()
    q.join()


if __name__ == '__main__':
    main()
