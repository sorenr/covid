#!/bin/env python3

"""
Run this script on the "Daily Deaths" JSON data from
https://coronavirus.data.gov.uk/details/deaths
Or use the uk_deaths.json file included here
"""

import sys
import json
import dateutil
import argparse
import numpy
import matplotlib.pyplot as plt

ALL = "United Kingdom"
ENGLAND = "England"
N_IRELAND = "Northern Ireland"
SCOTLAND = "Scotland"
WALES = "Wales"

POPULATIONS = {
    ENGLAND: 55.98,
    N_IRELAND: 1.885,
    SCOTLAND: 5.454,
    WALES: 3.136
}
POPULATIONS[ALL] = sum(POPULATIONS.values())

LOCKDOWNS = [
    [dateutil.parser.parse('March 23 2020'),
     dateutil.parser.parse('July 4 2020')],
    [dateutil.parser.parse('November 5 2020'),
     dateutil.parser.parse('December 3 2020')]
]

XTICKS = 16
FIGSIZE = (12, 9)
DPI = 200


def read_deaths(data: list):
    deaths = {}
    for i, row in enumerate(data):
        nation = row['areaName']
        date = dateutil.parser.parse(row['date'])
        deaths_new = row['newDeaths28DaysByDeathDate']
        if deaths_new is None:
            continue
        nation_dates = deaths.setdefault(date, {})
        nation_dates[nation] = deaths_new
    return deaths


def normalize_deaths(deaths: dict):
    days = list(sorted(deaths.keys()))
    day_first = days[0]
    days_total = (days[-1] - day_first).days + 1
    series = numpy.array([(d - day_first).days for d in days], dtype=numpy.int32)
    data = numpy.zeros(shape=(5, days_total), dtype=numpy.int32)
    nations = {}
    for i, day in enumerate(days):
        si = series[i]
        for nation, nation_deaths in deaths[day].items():
            nation_i = nations.setdefault(nation, len(nations))
            data[nation_i][si] = nation_deaths
    # Add a nation entry for the UK
    nation_i = nations.setdefault(ALL, len(nations))
    # Put the sum in the last row
    data[nation_i] = data[:nation_i].sum(axis=0)
    return days, nations, series, data


def derivatives(series: numpy.array, data: numpy.array):
    dData = data[:, 1:] - data[:, :-1]
    dSeries = series[1:] - series[:-1]
    return series[:-1], numpy.true_divide(dData, dSeries)


def smooth(w: int, data: numpy.array):
    rv = numpy.zeros_like(data, dtype=numpy.float32)
    cf = numpy.ones(w)
    for i in range(data.shape[0]):
        rv[i] = numpy.convolve(data[i], cf, mode="same") / w
    return rv


def plot_lockdowns(ax, date_start):
    for ld_start, ld_end in LOCKDOWNS:
        ax.axvline(x=(ld_start - date_start).days, c='r', linewidth=1)
        ax.axvline(x=(ld_end - date_start).days, c='g', linewidth=1)


def add_ticks(fig, nticks: int, series: list, dates: list):
    locs = []
    labels = []
    for i in range(series[0], series[-1]+1, int(len(series)/(nticks-1))):
        locs.append(series[i])
        labels.append(dates[i].strftime('%m/%d'))
    fig.xticks(locs, labels)


def plot_deaths(days: list, nations: dict, series: numpy.array, data: numpy.array):
    data = smooth(7, data)

    d_series, d_nations = derivatives(series, data)

    # for each nation...
    for nation, nation_i in sorted(nations.items()):
        # plot the national deaths
        fig = plt.figure(nation, figsize=FIGSIZE)
        fig.suptitle(nation, fontsize=16)
        plt.figtext(
            0.02, 0.02,
            "Data: coronavirus.data.gov.uk/details/deaths\n"
            "Source: github.com/sorenr/covid/blob/main/uk_deaths.py",
            fontsize=10)
        ax1 = fig.add_subplot(211)
        ax1.set_ylabel('deaths')
        ax1.bar(
            series, data[nation_i],
            width=1)
        plot_lockdowns(ax1, days[0])
        add_ticks(plt, XTICKS, series, days)

        # plot the national death derivatives
        ax2 = fig.add_subplot(212)
        ax2.set_ylabel('dDeath/dTime')
        ax2.plot(d_series, d_nations[nation_i])
        ax2.axhline(y=0, linewidth=1, c='b')
        plot_lockdowns(ax2, days[0])
        add_ticks(plt, XTICKS, series, days)

        plt.savefig("{0:s}.png".format(nation), dpi=DPI)
    # plt.show()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        deaths = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r') as fd:
            deaths = fd.read()

    deaths = json.loads(deaths)
    deaths = read_deaths(deaths['data'])
    days, nations, series, data = normalize_deaths(deaths)
    plot_deaths(days, nations, series, data)
