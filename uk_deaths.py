#!/bin/env python3

"""
Run this script on the "Daily Deaths" JSON data from
https://coronavirus.data.gov.uk/details/deaths
Or use the uk_deaths.json file included here
"""

import sys
import json
import dateutil
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
    series = []
    nations = {ALL: [0] * days_total}
    for day in days:
        day_diff = (day - day_first).days
        series.append(day_diff)
        all_deaths = 0
        for nation, nation_deaths in deaths[day].items():
            if nation not in nations:
                nations[nation] = [0] * days_total
            nations[nation][day_diff] = nation_deaths
            all_deaths += nation_deaths
        nations[ALL][day_diff] = all_deaths
    return series, days, nations


def derivatives(series: list, nations: dict):
    d_series = []
    d_nations = {}
    for i in range(1, len(series)-1):
        d_series.append(series[i])
        for nation, deaths in nations.items():
            dDdT = (deaths[i+1] - deaths[i-1]) / (series[i+1] - series[i-1])
            d_nations.setdefault(nation, []).append(dDdT)
    return d_series, d_nations


def plot_lockdowns(ax, date_start):
    for ld_start, ld_end in LOCKDOWNS:
        ax.axvline(x=(ld_start - date_start).days, c='r', linewidth=1)
        ax.axvline(x=(ld_end - date_start).days, c='g', linewidth=1)


def plot_deaths(series: list, days: list, nations: dict):
    d_series, d_nations = derivatives(series, nations)

    # for each nation...
    for nation in sorted(nations.keys()):
        # plot the national deaths
        fig = plt.figure(nation, figsize=(11,8))
        fig.suptitle(nation, fontsize=16)
        plt.figtext(
            0.02, 0.02,
            "Data: coronavirus.data.gov.uk/details/deaths\n"
            "Source: github.com/sorenr/covid/blob/main/uk_deaths.py",
            fontsize=10)
        ax1 = fig.add_subplot(211)
        ax1.set_ylabel('deaths')
        ax1.bar(
            series, nations[nation],
            width=1)
        plot_lockdowns(ax1, days[0])

        # plot the national death derivatives
        ax2 = fig.add_subplot(212)
        ax2.set_ylabel('dDeath/dTime')
        ax2.plot(d_series, d_nations[nation])
        ax2.axhline(y=0, linewidth=1, c='b')
        plot_lockdowns(ax2, days[0])
        plt.savefig("{0:s}.png".format(nation), dpi=200)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        deaths = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r') as fd:
            deaths = fd.read()

    deaths = json.loads(deaths)
    deaths = read_deaths(deaths['data'])
    series, days, nations = normalize_deaths(deaths)
    plot_deaths(series, days, nations)
