#!/bin/env python3

"""
Run this script on the "Daily Deaths" JSON data from
https://coronavirus.data.gov.uk/details/deaths
Or use the uk_data.json file included here
"""

import os
# import dateutil
import argparse
# import numpy
import pandas
import matplotlib.pyplot as plt


DAYS = "DAYS"
VAERS_ID = "VAERS_ID"
VAX_DATE = "VAX_DATE"
VAX_TYPE = "VAX_TYPE"
ONSET_DATE = "ONSET_DATE"

GLOBAL_OFFSET = 1

YEAR = 365.25
XLABELS = {
    "vax": 0,
    "1 day": 1,
    "1 week": 7,
    "1 month": YEAR/12,
    "1 year": YEAR,
    "10 years": YEAR * 10
}


def add_data(data, vax_type, days):
    """Add a report to the appropriate vax's onset bin"""
    row = data.setdefault(vax_type, {})
    row[days] = 1 + row.get(days, 0)


def parse(vax_files, symptoms=None):
    # filter out the core vax records
    vax_files = [x for x in vax_files if x.endswith('VAERSVAX.csv')]

    vax_data = {}

    # for each vax file
    for vax_file in vax_files:
        # load the core vax record
        vax_data_csv = pandas.read_csv(vax_file, encoding='latin1', low_memory=False)

        # infer the path to the data record
        vax_path = os.path.split(vax_file)

        if symptoms:
            symptom_path = vax_path[-1].split('VAERS')[0]+'VAERSSYMPTOMS.csv'
            symptom_path = os.path.join(vax_path[0], symptom_path)
            symptom_data = pandas.read_csv(symptom_path, encoding='latin1', low_memory=False)

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

            # restrict reports to specific symptoms
            if symptoms:
                symptom_row = [x.lower() for x in symptom_data.loc[vax_id] if isinstance(x, str)]
                symptom_match = False
                for sm in symptoms:
                    symptom_match = sm in symptom_row
                    if symptom_match:
                        break
                if not symptom_match:
                    continue
                print(symptom_row)

            vax_type = vax_data_csv[VAX_TYPE][vax_id]
            add_data(vax_data, vax_type, onset_i.days)

    return vax_data


def plot(vax_data, args, title="Adverse Reaction"):
    """Plot symptom onset frequency"""
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
    if args.prevax:
        vax_onsets = range(-1, days_min - 1, -1)
    else:
        vax_onsets = range(0, days_max + 1)

    plt.figure(num=1, figsize=(11, 7))

    ymax = 0
    reports = 0

    for row_i, row in enumerate(sorted(vax_frequency.items(), reverse=True, key=lambda kv: kv[1])):
        if row_i > 30:
            break
        # get values from the row
        vax_name = row[0]
        vax_dt = vax_data[vax_name]
        print(vax_frequency[vax_name], vax_name, "reports", min(vax_dt.keys()), "-", max(vax_dt.keys()), "days")
        x = [0]
        y = [0]
        for i in vax_onsets:
            reports_t = vax_dt.get(i, 0)
            reports += reports_t
            yt = 100 * reports_t / vax_frequency[vax_name]
            if not y or y[-1] or yt:
                it = abs(i)
                if x and x[-1] < it - 1:
                    x.append(it - 1)
                    y.append(0.0)
                ymax = max(ymax, yt)
                x.append(it)
                y.append(yt)
        plt.plot([i + GLOBAL_OFFSET for i in x], y, label=vax_name)
    plt.xscale("log")
    # enable this for log scale y
    yscale = 0.95
    if args.ylog:
        yscale = pow(yscale, 10)
        plt.yscale("log")
        plt.ylim(0.001, ymax)
    else:
        plt.ylim(0, ymax)
    plt.ylabel("% Adverse Reactions")
    plt.vlines([x + GLOBAL_OFFSET for x in XLABELS.values()], 0, ymax * yscale, linestyles="dotted")
    plt.legend(fontsize="x-small")
    if args.prevax:
        plt.xlabel(f"{title} Onset (-Days)")
        plt.gca().invert_xaxis()
        plt.title(f'VAERS Adverse Reactions Misreported Before Vaccination ({reports:,} Misreports)')
        sign_prevax = '-'
        ha = 'right'
    else:
        plt.xlabel(f"{title} Onset (Days)")
        plt.title(f'VAERS Adverse Reactions Reported After Vaccination ({reports:,} Reports)')
        sign_prevax = ''
        ha = 'left'
    for label, label_x in XLABELS.items():
        if label_x:
            label_t = sign_prevax + label
            ha_t = ha
        else:
            label_t = label
            ha_t = "center"
        plt.text(label_x + GLOBAL_OFFSET, ymax * yscale, label_t, color="blue", ha=ha_t)


def main():
    parser = argparse.ArgumentParser(description="Plot VAERS onset data.")
    parser.add_argument('--symptoms', type=str, nargs="+", help="filter symptoms")
    parser.add_argument('--prevax', action="store_true", help="show pre-vaccination reports (reactions before vaccination)")
    parser.add_argument('--ylog', action="store_true", help="plot Y axis in log")
    parser.add_argument('stats', metavar='DATA.csv', type=str, nargs="+",
                        help='CSV files from https://vaers.hhs.gov/data/datasets.html')

    args = parser.parse_args()

    vax_data = parse(args.stats, args.symptoms)

    title = "Adverse Reaction"
    if args.symptoms:
        title = ",".join([x.capitalize() for x in parser.symptoms])

    plot(vax_data, args, title=title)

    plt.show()


if __name__ == "__main__":
    main()
