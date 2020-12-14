#!/usr/bin/env python3

"""
Plot country policy data available at
https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv
"""

import sys
import argparse
import pprint
import enum
import csv
import numpy
import matplotlib.pyplot as plt

import covid


URL = "https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest_withnotes.csv"
DATA_FILE = "oxgcrt_latest_withnotes.csv"


XTICKS = 8
FIGSIZE = (15, 4)
DPI = 200

TOTAL_NAT = "NAT_TOTAL"
TOTAL_STATE = "STATE_TOTAL"


I_DATE = 5
I_COUNTRY_NAME = 0
I_COUNTRY_CODE = 1
I_REGION_NAME = 2
I_REGION_CODE = 3
I_JUSRISDICTION = 4


class Metric(enum.Enum):
    SCHOOL = 6
    WORK = 9
    EVENTS = 12
    GATHERING = 15
    TRANSPORT = 18
    HOME = 21
    MOVEMENT = 24
    IMMIGRATION = 27
    INCOME = 29
    DEBT = 32
    FISCAL = 34
    MASKS = 49
    VACCINATION = 52
    STRINGENCY = 59


class OxCGRT:
    data = None
    arr = None

    def __read_data(self, fname):
        """Parse the CSV file."""
        with open(fname, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            self.data = list(reader)

    def __normalize_data(self):
        """Transform data from CSV to numpy array."""
        self.heading = self.data[0]
        for i, h in enumerate(self.heading):
            print(i, h)
        print()

        self.data = self.data[1:]
        self.country_code = {}
        self.code_name = {}
        self.dates = set()
        for row in self.data:
            self.code_name[row[I_COUNTRY_CODE]] = row[I_COUNTRY_NAME]
            country = self.country_code.setdefault(row[I_COUNTRY_NAME],
                                                   (row[I_COUNTRY_CODE], {}))
            if row[I_JUSRISDICTION] == TOTAL_STATE:
                country[1][row[I_REGION_NAME]] = row[I_REGION_CODE]
                self.code_name[row[I_REGION_CODE]] = row[I_REGION_NAME]
            self.dates.add(row[I_DATE])

        pprint.pprint(self.country_code)
        print()

        if not args.code:
            sys.exit(-1)

        # name_idx = index(sorted(code_name.values()))
        self.codes = list(sorted(self.code_name.keys()))
        self.code_idx = covid.index(self.codes)
        self.dates = list(sorted(self.dates))
        self.date_idx = covid.index(self.dates)
        self.metric_idx = covid.index([x.name for x in Metric])

        self.arr = numpy.zeros((len(self.code_idx), len(Metric), len(self.date_idx)),
                               dtype=numpy.float32)

        for row in self.data:
            for metric in Metric:
                val = row[metric.value]
                if not val:
                    continue
                i_code = self.code_idx[row[I_COUNTRY_CODE]]
                i_metric = self.metric_idx[metric.name]
                i_date = self.date_idx[row[I_DATE]]
                self.arr[i_code, i_metric, i_date] = val

    def get(self, code, metric):
        i_code = self.code_idx[code]
        try:
            i_metric = self.metric_idx[metric]
        except KeyError:
            print("Metrics:")
            for metric in sorted(self.metric_idx):
                print(metric)
            sys.exit(-1)
        return self.arr[i_code, i_metric]

    def __init__(self, fname):
        self.__read_data(fname)
        self.__normalize_data()


def oxgcrt(args):
    covid.download(URL, DATA_FILE, shelf_life=60*60*24)

    oxgcrt = OxCGRT(DATA_FILE)

    figsize = (FIGSIZE[0], FIGSIZE[1] * len(args.metric))
    fig = plt.figure("OxCGRT", figsize=figsize)
    fig.subplots_adjust(left=0.05, right=0.98)
    for i_metric, metric in enumerate(args.metric):
        metric = metric.upper()
        ax = fig.add_subplot(len(args.metric), 1, i_metric + 1,
                             xmargin=0)
        ax.set_ylabel("OxCGRT "+metric.capitalize())
        for code in args.code:
            row = oxgcrt.get(code, metric)
            label = oxgcrt.code_name[code]
            ax.plot(range(len(oxgcrt.dates)), row, label=label)
        covid.add_ticks(plt, XTICKS, range(len(oxgcrt.dates)), oxgcrt.dates)
        if len(args.code) > 1:
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot country policy data.")
    parser.add_argument('--metric', nargs='+', type=str, default=['STRINGENCY'], help='Metric to use')
    parser.add_argument('--png', type=str, help='store to PNG')
    parser.add_argument('code', type=str, nargs='+',
                        help='Country or region codes to plot')

    args = parser.parse_args()

    oxgcrt(args)
