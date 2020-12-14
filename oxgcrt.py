#!/usr/bin/env python3

"""
Plot country policy data available at
https://raw.githubusercontent.com/OxCGRT/covid-policy-scratchpad/master/risk_of_openness_index/data/riskindex_timeseries_latest.csv
"""

import sys
import argparse
import csv
import numpy
import matplotlib.pyplot as plt


def read_data(fname):
    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        data = list(reader)
    return data


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


def oxgcrt(args):
    data = read_data(args.fname)

    # heading = data[0]
    data = data[1:]
    name_code = {x[2]: x[1] for x in data}

    if not args.countries:
        for name, code in sorted(name_code.items()):
            print(code, name)
        sys.exit(-1)

    code_name = {x[1]: x[2] for x in data}
    country_idx = index(sorted(code_name.values()))
    dates = list(sorted(set([x[3] for x in data])))
    date_idx = index(sorted(dates))

    arr = numpy.zeros((len(country_idx), len(dates)), dtype=numpy.float32)

    for row in data:
        # skip "NA" cells
        if row[9] == "NA":
            continue
        country = row[2]
        date = row[3]
        arr[country_idx[country], date_idx[date]] = row[9]

    fig, ax = plt.subplots()
    ax.set_ylabel('OxCGRT openness_risk')
    for code in args.countries:
        country = code_name[code]
        ci = country_idx[country]
        ax.plot(range(len(dates)), arr[ci], label=country)
    add_ticks(plt, 4, range(len(dates)), dates)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot country policy data.")
    parser.add_argument('--png', type=str, help='store to PNG')
    parser.add_argument('--countries', type=str, nargs='+', help='Countries to plot')
    parser.add_argument('fname', metavar='STATS.csv', type=str,
                        help='CSV file from https://raw.githubusercontent.com/OxCGRT/covid-policy-scratchpad/master/risk_of_openness_index/data/riskindex_timeseries_latest.csv')

    args = parser.parse_args()

    oxgcrt(args)
