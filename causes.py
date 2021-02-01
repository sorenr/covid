import csv
import pprint
import operator
import matplotlib.pyplot as plt
import numpy

conditions = {}
categories = {}

with open('causes.csv', newline='') as csvfile:
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

        if condition in conditions:
            conditions[condition] += int(ndeaths)
        else:
            conditions[condition] = int(ndeaths)

        if category in categories:
            categories[category] += int(ndeaths)
        else:
            categories[category] = int(ndeaths)

d = float(conditions['COVID-19'])

cond_labels = []
cond_data = []

for row in sorted(conditions.items(), key=operator.itemgetter(1), reverse=True):
    print(row[1], row[0])
    cond_labels.append(row[0])
    cond_data.append(row[1]/1000)

print()
print((sum(conditions.values()) - d) / d)

plt.rcdefaults()
fig, ax = plt.subplots()

y_pos = numpy.arange(len(cond_data))

ax.barh(y_pos, cond_data, align='center')
ax.set_yticks(y_pos)
ax.set_yticklabels(cond_labels)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Fatal Cases (thousands)')
ax.set_title('SARS-CoV-2 Comorbidities')

plt.subplots_adjust(left=0.4)
plt.show()
