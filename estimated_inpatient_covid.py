#!/usr/bin/env python3

"""
Plot state ICU usage from data at
https://healthdata.gov/dataset/covid-19-estimated-patient-impact-and-hospital-capacity-state
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


def estimate_inpatient(args):
    data = read_data(args.fname)

    # heading = data[0]
    data = data[1:]
    states = list(sorted(set([x[0] for x in data])))
    states_idx = index(states)
    dates = list(sorted(set([x[1] for x in data])))
    dates_idx = index(dates)

    arr = numpy.zeros((len(states), len(dates), 2), dtype=numpy.float32)

    for row in data:
        state = row[0]
        date = row[1]
        use = float(row[2].replace(',', ''))
        beds = float(row[8].replace(',', ''))
        arr[states_idx[state], dates_idx[date]] = [use, beds]

    if args.state is None:
        patients = numpy.sum(arr, axis=0)
    else:
        patients = arr[states_idx[args.state.upper()]]
    pct = 100 * numpy.true_divide(patients[:, 0], patients[:, 1])

    for pair in zip(dates, pct):
        print(pair)

    fig, ax = plt.subplots()
    ax.set_ylabel('% COVID admissions')
    if args.state is None:
        ax.set_title('All States')
    else:
        ax.set_title('State = {0:s}'.format(args.state.upper()))
    ax.plot(range(len(dates)), pct)
    add_ticks(plt, 4, range(len(dates)), dates)
    ax.axvline(x=dates_idx['2020-11-15'], c='r', linewidth=1)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot COVID hospital admissions.")
    parser.add_argument('--interactive', action='store_true', help='display charts interactively')
    parser.add_argument('--state', type=str, help='State to plot')
    parser.add_argument('fname', metavar='STATS.csv', type=str,
                        help='CSV file from https://healthdata.gov/dataset/covid-19-estimated-patient-impact-and-hospital-capacity-state')

    args = parser.parse_args()

    estimate_inpatient(args)
