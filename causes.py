import csv
import sys
import matplotlib.pyplot as plt
import numpy
from numpy.core.fromnumeric import size


def add_cat(table, category, ndeaths, nmentions):
    """Add a category to the table."""
    (odeaths, omentions) = table.get(category, (0, 0))
    table[category] = (odeaths + int(ndeaths), omentions + int(nmentions))


def get_data(fname):
    """Parse fname and return the condition and category data."""
    conditions = {}
    categories = {}

    # open and read the CSV file
    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            as_of, wk_start, wk_end, group, year, month, state, category, condition, icd10, age, ndeaths, mentions, flag = row

            # only consider "all ages"
            if age.lower() != "all ages":
                continue

            # skip rows with zero deaths
            if not ndeaths:
                continue

            # add national totals, disregard state totals 
            if state != "United States":
                continue

            # add total totals, disregard yearly and montly totals
            if group != "By Total":
                continue

            try:
                ndeaths = int(ndeaths)
            except ValueError:
                continue

            add_cat(conditions, condition, ndeaths, mentions)
            add_cat(categories, category, ndeaths, mentions)

    return conditions, categories


def make_totals(data, divisor=1):
    """Return a ranked list of total deaths. (chart 1)"""
    rv = []
    for category, (ndeaths, nmentions) in data.items():
        rv.append((ndeaths/divisor, (nmentions-ndeaths)/divisor, category))
    return list(sorted(rv, reverse=True))


def make_percents(data):
    """Return a ranked list of COVID percentages. (chart 2)"""
    rv = []
    for category, (ndeaths, nmentions) in data.items():
        rv.append((100 * ndeaths / nmentions, category))
    return list(sorted(rv, reverse=True))


def abbrev(val):
    val = float(val)
    if val > 1000:
        val /= 1000
        return f"{val:0.0f}k"
    return f"{val:0.0f}"


def plot_deaths(table):
    # sort rows by deaths (descending)
    table_sorted = sorted([(v, k) for k, v in table.items()], reverse=True)
    data = []
    labels = []
    for row_data, row_label in table_sorted:
        data.append(row_data)
        labels.append(row_label)
    data = numpy.array(data, dtype=numpy.uint32)
    # data = numpy.divide(data, 1000)

    print("L:", labels)
    y_pos = numpy.arange(len(labels))

    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(11, 5))

    # Example data
    y_pos = numpy.arange(len(labels))

    div = 1000
    ax.barh(y_pos, data[:, 1] / div, label="Without COVID-19", align='center')
    ax.barh(y_pos, data[:, 0] / div, label="With COVID-19", align='center')

    ax.legend(fontsize='small')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # labels read top-to-bottom

    # add labels
    ax.set_title('Death Certificate Comorbidities')
    ax.set_xlabel('Total Mentions (Thousands)')

    # add per-row data labels
    for i in range(len(data)):
        f = data[i, 1]  # full count
        m = data[i, 0]  # mentions
        lbl = abbrev(m) + " : " + abbrev(f - m)
        plt.text(f / div + 10, i + 0.25, lbl, size="small")

    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1, x2 * 1.1, y1, y2))
    plt.subplots_adjust(left=0.5, right=0.99)
    plt.show()
    sys.exit(-1)


if __name__ == "__main__":
    # download causes.csv from
    # https://data.cdc.gov/NCHS/Conditions-Contributing-to-COVID-19-Deaths-by-Stat/hk9y-quqm
    conditions, categories = get_data(sys.argv[1])

    # plot_example()
    plot_deaths(conditions)

    # percents = make_percents(conditions)
    # plot_data(
    #     title='Percentage of COVID-19 Deaths, by Comorbidity',
    #     xlabel='Case Association (percent)',
    #     data=percents)
