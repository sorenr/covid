#!/bin/env python3

"""
Run this script on the "Daily Deaths" JSON data from
https://coronavirus.data.gov.uk/details/deaths
Or use the uk_data.json file included here
"""

import os
import operator
# import dateutil
import datetime
import argparse
import numpy
# import numpy
import pandas
import matplotlib.pyplot as plt


DAYS = "DAYS"
VAERS_ID = "VAERS_ID"
VAX_DATE = "VAX_DATE"
VAX_TYPE = "VAX_TYPE"
ONSET_DATE = "ONSET_DATE"


def add_data(data, vax_type, days):
    row = data.setdefault(vax_type, {})
    row[days] = 1 + row.get(days, 0)


def main():
    parser = argparse.ArgumentParser(description="Plot VAERS onset data.")
    parser.add_argument('stats', metavar='DATA.json', type=str, nargs="+",
                        help='JSON file from https://coronavirus.data.gov.uk/details/deaths')

    args = parser.parse_args()

    # filter out the core vax records
    vax_files = [x for x in args.stats if x.endswith('VAERSVAX.csv')]

    vax_data = {}
    early_data = {}

    # for each vax file
    for vax_file in vax_files:
        # load the core vax record
        vax_data_csv = pandas.read_csv(vax_file, encoding='latin1', low_memory=False)

        # infer the path to the data record
        vax_path = os.path.split(vax_file)
        detail_path = vax_path[-1].split('VAERS')[0]+'VAERSDATA.csv'
        detail_path = os.path.join(vax_path[0], detail_path)
        detail_data = pandas.read_csv(detail_path, encoding='latin1', low_memory=False)
        # print(vax_data.keys())
        # print(detail_data.keys())

        # compute the onset time
        vax_date = pandas.to_datetime(detail_data[VAX_DATE])
        onset_date = pandas.to_datetime(detail_data[ONSET_DATE])
        onset = onset_date - vax_date

        # add each record to vax_data
        for vax_id, onset_i in onset.items():
            # ignore null dates (missing vax or onset date)
            if pandas.isnull(onset_i):
                continue
            vax_type = vax_data_csv[VAX_TYPE][vax_id]
            if onset_i.days < 0:
                print(onset_i.days, detail_data[VAX_DATE][vax_id], detail_data[ONSET_DATE][vax_id])
                add_data(early_data, vax_type, onset_i.days)
            else:
                add_data(vax_data, vax_type, onset_i.days)

    # for row in sorted(early_data.items(), reverse=True, key=lambda kv: sum(kv[1])):
    #     print(row)

    days_min = 99999
    days_max = -days_min
    vax_frequency = {}  # records per vaccination

    # count total frequency
    for vax_name, vax_onsets in vax_data.items():
        days_min = min(days_min, min(vax_onsets.keys()))
        days_max = max(days_max, max(vax_onsets.keys()))
        vax_frequency[vax_name] = sum(vax_onsets.values())

    print("MIN", days_min)
    print("MAX", days_max)
    vax_onsets = range(days_min, days_max+1)

    plt.figure(num=1, figsize=(11, 7))

    ymax = 0
    reports = 0

    for row_i, row in enumerate(sorted(vax_frequency.items(), reverse=True, key=lambda kv: kv[1])):
        if row_i > 30:
            break
        # get values from the row
        vax_name = row[0]
        vax_dt = vax_data[vax_name]
        x = [0]
        y = [0]
        for i in range(days_min, days_max + 1):
            reports += vax_dt.get(i, 0)
            yt = vax_dt.get(i, 0) / vax_frequency[vax_name]
            if not y or y[-1] or yt:
                if x and x[-1] < i-1:
                    x.append(i-1)
                    y.append(0.0)
                if ymax <= yt:
                    print(vax_name, i, yt)
                    ymax = yt
                x.append(i)
                y.append(yt)
        plt.plot([i+1 for i in x], y, label=vax_name)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Adverse Reaction Onset (Days)")
    plt.ylabel("% Adverse Reactions")
    plt.ylim(0, ymax)
    plt.legend(fontsize="x-small")
    plt.title(f'Symptom Onset (Days) From {reports:,} VAERS Reports')
    plt.show()


if __name__ == "__main__":
    main()
