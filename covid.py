import os
import time
import pathlib
import urllib.request
import subprocess


def get_http(url, dest):
    """Retrieve a file via http"""
    print("HTTP", url)
    if not os.path.exists(dest):
        return urllib.request.urlretrieve(url, dest)


def get_curl(url, dest):
    """Retrieve a file via curl"""
    print("CURL", url)
    subprocess.run(["curl", url, "-o", dest], check=True)


def download(url, dest, shelf_life=None):
    """Download the URL to the destination."""
    dest_tmp = dest
    dest_info = pathlib.Path(dest)
    if dest_info.exists():
        if shelf_life is None:
            print(dest, "already exists.")
            return
        age = time.time() - dest_info.stat().st_ctime
        if age < shelf_life:
            print(dest, ": {0:0.1f}".format(age), "<", shelf_life)
            return
        else:
            print(dest, ": {0:0.1f}".format(age), ">", shelf_life)
            dest_tmp = dest + ".tmp"
    if get_http(url, dest_tmp):
        if dest_tmp != dest:
            os.rename(dest_tmp, dest)


def index(lst):
    """Return a dictionary of index locations."""
    return {i: x for x, i in enumerate(lst)}


def add_ticks(plt, nticks: int, series: list, labels: list):
    locs = []
    lbls = []
    for i in range(series[0], series[-1]+1, int(len(series)/(nticks-1))):
        locs.append(series[i])
        lbls.append(labels[i])
    plt.xticks(locs, lbls)
