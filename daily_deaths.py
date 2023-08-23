import os
import sys
import numpy
import pandas
import matplotlib.pyplot as plt

DEATH_COL = "newDailyNsoDeathsByDeathDate"
DATE_COL = "date"
YEAR_START = 2020


def daily_deaths(death_csv):
    death_data = pandas.read_csv(death_csv, encoding='latin1', low_memory=False)

    # make columns
    dates = pandas.to_datetime(death_data[DATE_COL]).dt
    days = dates.day_of_year

    years = dates.year
    years_unique = years.unique()
    years_unique.sort()
    year_max = years_unique[-1]
    date_max = (year_max, 0)

    data = numpy.zeros([days.max(), len(years.unique())], dtype=numpy.int32)

    for index, row in death_data.iterrows():
        day = days[index] - 1
        year = years[index] - YEAR_START
        date_max = max(date_max, (dates.year[index], day))
        data[day, year] = row[DEATH_COL]

    # sum = numpy.zeros([len(years)], dtype=data.dtype)
    sum = numpy.zeros_like(data[0])
    sums = numpy.zeros_like(data)

    for i, row in enumerate(data):
        sum = numpy.add(sum, row)
        sums[i] = sum

    data_pd = pandas.DataFrame(data=sums, columns=years_unique)

    for day in range(date_max[1]+1, 366):
        data_pd.at[day, year_max] = pandas.NA

    fig = plt.figure(dpi=300)

    ax = data_pd.plot(kind='line',
                       title='UK COVID Death Certificates By Year',
                       grid=True,
                       figsize=(7,4),
                       xlabel="Day of Year",
                       ax=plt.gca())

    res = ax.get_figure()

    output = os.path.splitext(death_csv)[0]+'.png'
    res.savefig(output)


if __name__ == "__main__":
    daily_deaths(sys.argv[1])
