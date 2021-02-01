import csv
import pprint
import operator
import matplotlib.pyplot as plt
import numpy

def add_cat(table, category, ndeaths, nmentions):
    """Add a category to the table."""
    new_data = (int(ndeaths), int(nmentions))
    if category in table:
        table[category] = table[category] + new_data
    else:
        table[category] = new_data


def get_data(fname):
    """Parse fname and return the condition and category data."""
    conditions = {}
    categories = {}

    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            as_of, wk_start, wk_end, state, category, condition, icd10, age, ndeaths, mentions, flag = row

            # disregard "all ages"
            if age.lower() != "all ages":
                continue

            # disregard no deaths
            if not ndeaths:
                continue

            if state != "US":
                continue

            try:
                ndeaths = int(ndeaths)
            except ValueError:
                continue

            add_cat(conditions, condition, ndeaths, mentions)
            add_cat(categories, category, ndeaths, mentions)

    return conditions, categories


def make_totals(data, divisor=1000):
    """Return a ranked list of total deaths."""
    rv = []
    for category, vals in data.items():
        rv.append((vals[0]/divisor, category))
    return list(sorted(rv, reverse=True))


def make_percents(data):
    """Return a ranked list of COVID percentages."""
    rv = []
    for category, vals in data.items():
        rv.append((100 * vals[0] / vals[1], category))
    return list(sorted(rv, reverse=True))


def plot_data(title, xlabel, data):
    values, labels = zip(*data)
    pprint.pprint(data)

    plt.rcdefaults()
    fig, ax = plt.subplots()

    y_pos = numpy.arange(len(labels))

    ax.barh(y_pos, values, align='center')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel(xlabel)
    ax.set_title(title)

    plt.subplots_adjust(left=0.4)
    plt.show()


if __name__ == "__main__":
    conditions, categories = get_data('causes.csv')

    totals = make_totals(conditions)
    plot_data(
        title='Comorbidities Mentioned in Conjunction With COVID-19 Deaths',
        xlabel='Total Mentions (thousands)',
        data=totals)

    percents = make_percents(conditions)
    plot_data(
        title='Comorbidities Mentioned in Conjunction With COVID-19 Deaths',
        xlabel='Case Association (percent)',
        data=percents)
