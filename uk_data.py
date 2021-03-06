#!/bin/env python3

"""
Run this script on the "Daily Deaths" JSON data from
https://coronavirus.data.gov.uk/details/deaths
Or use the uk_data.json file included here
"""

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

LOCKDOWNS = {
    ENGLAND: [
        [dateutil.parser.parse('March 23 2020'),
         dateutil.parser.parse('July 4 2020')],
        [dateutil.parser.parse('November 5 2020'),
         dateutil.parser.parse('December 3 2020')],
        [dateutil.parser.parse('January 4 2021'),
         dateutil.parser.parse('April 12 2021')]
     ],
    N_IRELAND: [
        [dateutil.parser.parse('October 16 2020'),
         dateutil.parser.parse('November 20 2020')],
        [dateutil.parser.parse('November 27 2020'),
         None]
     ],
    SCOTLAND: [
        [dateutil.parser.parse('October 23 2020'),
         dateutil.parser.parse('November 9 2020')],
        [dateutil.parser.parse('November 20 2020'),
         None]
     ],
    WALES: [
        [dateutil.parser.parse('October 23 2020'),
         dateutil.parser.parse('November 9 2020')],
     ]
}

XTICKS = 16
FIGSIZE = (14, 14)
DPI = 200


def read_data(table: list):
    data = {}
    for i, row in enumerate(table):
        nation = row['areaName']
        date = dateutil.parser.parse(row['date'])
        data_new = row['newDeaths28DaysByDeathDate']
        if data_new is None:
            continue
        nation_dates = data.setdefault(date, {})
        nation_dates[nation] = data_new
    return data


def normalize_data(data: dict):
    print(data)
    days = list(sorted(data.keys()))
    day_first = days[0]
    days_total = (days[-1] - day_first).days + 1
    series = numpy.array([(d - day_first).days for d in days], dtype=numpy.int32)
    arr = numpy.zeros(shape=(5, days_total), dtype=numpy.int32)
    nations = {}
    for i, day in enumerate(days):
        si = series[i]
        for nation, nation_data in data[day].items():
            nation_i = nations.setdefault(nation, len(nations))
            arr[nation_i][si] = nation_data
    # Add a nation entry for the UK
    nation_i = nations.setdefault(ALL, len(nations))
    # Put the sum in the last row
    arr[nation_i] = arr[:nation_i].sum(axis=0)
    return days, nations, series, arr


def percent_change_on_previous_day(series: numpy.array, data: numpy.array):
    day = data[:, 1:]
    previous = data[:, :-1]
    change = day - previous
    d = numpy.true_divide(change, previous)
    d /= series[1:] - series[:-1]
    return series[1:], d * 100


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


def plot_lockdowns(nation, ax, date_start):
    for ld_start, ld_end in LOCKDOWNS.get(nation, [[None, None]]):
        if ld_start is not None:
            ax.axvline(x=(ld_start - date_start).days, c='r', linewidth=1)
        if ld_end is not None:
            ax.axvline(x=(ld_end - date_start).days, c='g', linewidth=1)


def add_ticks(fig, nticks: int, series: list, dates: list):
    locs = []
    labels = []
    for i in range(series[0], series[-1]+1, int(len(series)/(nticks-1))):
        locs.append(series[i])
        labels.append(dates[i].strftime('%m/%d'))
    fig.xticks(locs, labels)


def plot_data(days: list, nations: dict, series: numpy.array, data: numpy.array, args):
    if args.smooth > 1:
        data = smooth(args.smooth, data)

    if args.pcopd:
        d_series, d_nations = percent_change_on_previous_day(series, data)
    else:
        d_series, d_nations = derivatives(series, data)

    # for each nation...
    for nation, nation_i in sorted(nations.items()):
        # plot the national deaths
        fig = plt.figure(nation, figsize=FIGSIZE)
        fig.suptitle(nation, fontsize=16, y=0.95)
        plt.figtext(
            0.02, 0.02,
            "Data: coronavirus.data.gov.uk/details/deaths\n"
            "Source: github.com/sorenr/covid/blob/main/uk_data.py",
            fontsize=10)
        ax1 = fig.add_subplot(211)
        ylabel = 'deaths'
        if args.smooth > 1:
            ylabel += ' ({0:d} day moving avg)'.format(args.smooth)
        ax1.set_ylabel(ylabel)
        ax1.bar(
            series, data[nation_i],
            width=1)
        plot_lockdowns(nation, ax1, days[0])
        if not args.interactive:
            add_ticks(plt, XTICKS, series, days)

        # plot the national death derivatives
        ax2 = fig.add_subplot(212)
        if args.pcopd:
            ax2.set_ylabel('% change on previous day')
        else:
            ax2.set_ylabel('dDeath/dTime')
        ax2.plot(d_series, d_nations[nation_i])
        ax2.axhline(y=0, linewidth=1, c='b')
        plot_lockdowns(nation, ax2, days[0])
        if not args.interactive:
            add_ticks(plt, XTICKS, series, days)

        if not args.interactive:
            plt.savefig("{0:s}.png".format(nation), dpi=DPI)

    if args.interactive:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot daily UK deaths from national statistics.")
    parser.add_argument('--smooth', metavar='W', type=int, default=1,
                        help='smooth the dataset')
    parser.add_argument('--interactive', action='store_true', help='display charts interactively')
    parser.add_argument('--pcopd', action='store_true', help='compute "% change on previous day" rather than derivative')
    parser.add_argument('stats', metavar='DATA.json', type=str,
                        help='JSON file from https://coronavirus.data.gov.uk/details/deaths')

    args = parser.parse_args()

    with open(args.stats, 'r') as fd:
        data = fd.read()

    data = json.loads(data)
    assert(data)
    data = read_data(data['data'])
    assert(data)
    days, nations, series, data = normalize_data(data)
    plot_data(days, nations, series, data, args)


if __name__ == "__main__":
    main()
