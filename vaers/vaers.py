#!/usr/bin/env python3

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
import re
import shelve
import matplotlib.pyplot as plt


DAYS = "DAYS"
VAERS_ID = "VAERS_ID"
VAX_DATE = "VAX_DATE"
VAX_TYPE = "VAX_TYPE"
ONSET_DATE = "ONSET_DATE"
REPORTS = "REPORTS"

GLOBAL_OFFSET = 1

# Any of these symptoms count as a death
SYMPTOMS_DEATH = {
    'agonal death struggle',
    'brain death',
    'cardiac death',
    'death',
    'death neonatal',
    'foetal death',
    'intra-uterine death',
    'sudden cardiac death',
    'sudden death',
    'sudden infant death syndrome'
}

YEAR = 365.25
XLABELS = {
    "vax": 0,
    "1 day": 1,
    "1 week": 7,
    "1 month": YEAR/12,
    "1 year": YEAR,
    "10 years": YEAR * 10
}

SYMPTOM_EXP = {
    'ageusia': 'ageusia (loss of taste)',
    'amnesia': 'amnesia (loss of memories)',
    'angioedema': 'angioedema (swelling under the skin)',
    'angiogram': 'angiogram (heart x-ray)',
    'anosmia': 'anosmia (loss of smell)',
    'aphasia': 'aphasia (difficulty with speech or language)',
    'apnoea': 'apnoea (breathing stops while you sleep)',
    'arthralgia': 'arthralgia (joint pain)',
    'asthenia': 'asthenia (lack of energy)',
    'atrial fibrillation': 'atrial fibrillation (irregular heart rate)',
    'cellulitis': 'cellulitis (skin infection)',
    'contusion': 'contusion (bruise)',
    'contusion': 'contusion (bruise)',
    'cyanosis': 'cyanosis (blue tint of the skin)',
    'deep vein thrombosis': 'deep vein thrombosis (blood clot)',
    'dermatitis bullous': 'dermatitis bullous (blisters)',
    'dysarthria': 'dysarthria (slurring words)',
    'diplopia': 'diplopia (double vision)',
    'dysgeusia': 'dysgeusia (altered perception of taste)',
    'dyskinesia': 'dyskinesia (involuntary twitching)',
    'dyspepsia': 'dyspepsia (indigestion)',
    'dysphagia': 'dysphagia (difficulty swallowing)',
    'dysphonia': 'dysphonia (abnormal voice)',
    'computerised tomogram': 'computerised tomogram (CT imaging/"CAT scan")',
    'dysstasia': 'dysstasia (difficulty standing)',
    'eye pruritus': 'eye pruritus (itchy eye)',
    'epistaxis': 'epistaxis (nosebleed)',
    'erythema': 'erythema (redness)',
    'face oedema': 'face oedema (swelling)',
    'herpes zoster': 'herpes zoster (cold sore)',
    'hemiparesis': 'hemiparesis (can\'t move one side of the body)',
    'hyperhidrosis': 'hyperhidrosis (excessive sweating)',
    'hypersomnia': 'hypersomnia (daytime sleepiness)',
    'hypertension': 'hypertension (high blood pressure)',
    'hypoacusis': 'hypoacusis (numbness)',
    'hypoaesthesia': 'hypoaesthesia (numbness)',
    'hypoaesthesia oral': 'hypoaesthesia oral (mouth numbness)',
    'hypokinesia': 'hypokinesia (limited range of movement)',
    'hypotension': 'hypotension (low blood pressure)',
    'hypotonia': 'hypotonia (decreased muscle tone)',
    'hypoxia': 'hypoxia (low oxygen)',
    'induration': 'induration (inflamed stiffness)',
    'injection site cellulitis': 'injection site cellulitis (skin infection)',
    'injection site erythema': 'injection site erythema (redness)',
    'injection site oedema': 'injection site oedema (swelling)',
    'injection site pruritus': 'injection site pruritus (itch)',
    'injection site urticaria': 'injection site urticaria (hives)',
    'insomnia': "insomnia (can't sleep)",
    'lacrimation increased': 'lacrimation increased (watering eyes)',
    'lethargy': 'lethargy (lack of energy)',
    'lymphadenopathy': 'lymphadenopathy (swollen lymph nodes)',
    'malaise': 'malaise (general discomfort)',
    'myalgia': 'myalgia (muscle pain)',
    'myocardial infarction': 'myocardial infarction (heart attack)',
    'nasopharyngitis': 'nasopharyngitis (common cold)',
    'neuralgia': 'neuralgia (sharp pain)',
    'ocular hyperemia': 'ocular hyperemia (red eyes)',
    'oedema': 'oedema (swelling)',
    'oedema peripheral': 'oedema peripheral (swelling)',
    'oropharyngeal pain': 'oropharyngeal pain (sore throat)',
    'pallor': 'pallor (pale appearance)',
    'pharyngeal paraesthesia': 'pharyngeal paraesthesia (false obstruction)',
    'photophobia': 'photophobia (light sensitivity)',
    'paraesthesia oral': 'paraesthesia oral (pins and needles)',
    'paraesthesia': 'paraesthesia (pins and needles)',
    'pharyngitis': 'pharyngitis (sore throat)',
    'parosmia': 'parosmia (distorted sense of smell)',
    'petechiae': 'petechiae (pinpoint spots)',
    'presyncope': 'presyncope (going to faint)',
    'pruritus': 'pruritus (itch)',
    'pulmonary embolism': 'pulmonary embolism (arterial blockage, lung)',
    'pyrexia': 'pyrexia (fever)',
    'rash erythematous': 'rash erythematous (inflamed capillaries)',
    'rash macular': 'rash macular (small red spots)',
    'rash maculo-papular': 'rash maculo-papular (small raised red bumps)',
    'rash papular': 'rash papular (bumpy rash)',
    'rash pruritic': 'rash pruritic (itchy rash)',
    'rash vesicular': 'rash vesicular (small blisters)',
    'rhinitis': 'rhinitis (cold, allergies)',
    'rhinorrhoea': 'rhinorrhoea (runny nose)',
    'somnolence': 'somnolence (feeling sleepy)',
    'syncope': 'syncope (fainting)',
    'tachycardia': 'tachycardia (fast heartbeat)',
    'thrombosis': 'thrombosis (blood clot in vein or artery)',
    'tinnitus': 'tinnitus (ringing in the ears)',
    'troponin': 'troponin (type of protein found in heart muscle)',
    'urticaria': 'urticaria (hives, rash)',
    'vasodilatation': 'vasodilatation (hot flushed skin)'
}

re_symptoms = re.compile(r'SYMPTOM[0-9]+$')


def add_data(data, vax_type, days):
    """Add a report to the appropriate vax's onset bin"""
    row = data.setdefault(vax_type, {})
    row[days] = 1 + row.get(days, 0)


def parse_onset(vax_data, deaths_unmatched, vax_data_csv, detail_data, symptom_data, args):
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
        if args.death:
            symptom_row = set([x.lower() for x in symptom_data.loc[vax_id] if isinstance(x, str)])
            symptom_match = symptom_row.intersection(SYMPTOMS_DEATH)
            # display symptoms matching death criteria
            # if symptom_match:
            #     print(symptom_match)
            if not symptom_match:
                ambiguous = {sr for sr in symptom_row if "death" in sr}
                for k in ambiguous:
                    deaths_unmatched[k] = deaths_unmatched.get(k, 0) + 1
            if not symptom_match:
                continue

        vax_type = vax_data_csv[VAX_TYPE][vax_id]
        add_data(vax_data, vax_type, onset_i.days)


def parse_vaxfreq(vax_data, vax_data_csv, detail_data, symptom_data, args):
    if 'ALL' in args.vaxfreq:
        vax_rows = vax_data_csv
    else:
        vax_rows = vax_data_csv[vax_data_csv[VAX_TYPE].isin(args.vaxfreq)]
    symptom_join = vax_rows.join(symptom_data.set_index(VAERS_ID), on=VAERS_ID)
    columns = [x for x in symptom_join.keys() if re_symptoms.match(x)]
    for i, row in symptom_join[columns].iterrows():
        row = {x.lower() for x in row if isinstance(x, str)}
        if args.symptoms:
            if not row.intersection(args.symptoms):
                continue
            if len(row) == 1:
                row.add('no other symptoms')
        vax_data[REPORTS] = vax_data.get(REPORTS, 0) + 1
        for symptom in row:
            vax_data[symptom] = vax_data.get(symptom, 0) + 1


def parse(vax_files, args):
    # filter out the core vax records
    vax_files = [x for x in vax_files if x.endswith('VAERSVAX.csv')]

    vax_data = {}
    deaths_unmatched = {}

    # for each vax file
    for vax_file in vax_files:
        # load the core vax record
        vax_data_csv = pandas.read_csv(vax_file, encoding='latin1', low_memory=False)

        # infer the path to the data record
        vax_path = os.path.split(vax_file)

        symptom_data = None
        if args.death or args.vaxfreq:
            symptom_path = vax_path[-1].split('VAERS')[0]+'VAERSSYMPTOMS.csv'
            symptom_path = os.path.join(vax_path[0], symptom_path)
            symptom_data = pandas.read_csv(symptom_path, encoding='latin1', low_memory=False)

        detail_path = vax_path[-1].split('VAERS')[0]+'VAERSDATA.csv'
        detail_path = os.path.join(vax_path[0], detail_path)
        detail_data = pandas.read_csv(detail_path, encoding='latin1', low_memory=False)
        # print(vax_data.keys())
        # print(detail_data.keys())

        if args.vaxfreq:
            parse_vaxfreq(vax_data, vax_data_csv, detail_data, symptom_data, args)
        else:
            parse_onset(vax_data, deaths_unmatched, vax_data_csv, detail_data, symptom_data, args)

    if deaths_unmatched:
        print("Uncounted Deathlike Events:")
        for k, v in sorted(deaths_unmatched.items(), reverse=True, key=lambda kv: kv[1]):
            print(k, v)

    return vax_data


def plot_onset(vax_data, args):
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

    plt.figure(num=1, figsize=(8, 8))

    ymax = 0
    reports = 0

    rows = args.n or 44

    for row_i, (vax_name, _) in enumerate(sorted(vax_frequency.items(), reverse=True, key=lambda kv: kv[1])):
        if row_i > rows:
            break
        # skip vaccines not listed
        if args.vax and vax_name not in args.vax:
            continue
        # get values from the row
        vax_dt = vax_data[vax_name]
        print(vax_frequency[vax_name], vax_name, "reports", min(vax_dt.keys()), "-", max(vax_dt.keys()), "days")
        x = [0]
        y = [0]

        if args.acc:
            yacc = 0
            for i in vax_onsets:
                yt = vax_dt.get(i, 0)
                yacc += yt
                if y[-1] != yacc:
                    x.append(i)
                    y.append(yacc)
            reports += y[-1]
            y = [yt / y[-1] * 100 for yt in y]
            ymax = 100
        else:
            for i in vax_onsets:
                yt = vax_dt.get(i, 0)
                reports += yt
                if y[-1] or yt:
                    it = abs(i)
                    if x and x[-1] < it - 1:
                        x.append(it - 1)
                        y.append(0.0)
                    yt /= vax_frequency[vax_name]
                    yt *= 100
                    ymax = max(ymax, yt)
                    x.append(it)
                    y.append(yt)

        plt.plot([i + GLOBAL_OFFSET for i in x], y, label=vax_name)

    title = "Event"
    fname = "vax_onset.png"
    if args.death:
        fname = "vax_death_onset.png"
        title = "Death"

    plt.xscale("log")
    # enable this for log scale y
    if args.ylog:
        yscale = pow(0.95, 10)
        plt.yscale("log")
        plt.ylim(0.001, ymax)
    else:
        yscale = 1.02
        plt.ylim(0, ymax * pow(yscale, 3))
    plt.ylabel(f"% {title}s")
    plt.vlines([x + GLOBAL_OFFSET for x in XLABELS.values()], 0, ymax * yscale, linestyles="dotted")
    if args.prevax:
        plt.legend(fontsize="x-small", loc="upper left")
        plt.xlabel(f"{title} Onset (-Days)")
        plt.gca().invert_xaxis()
        plt.title(f"VAERS {title}s Misreported Before Vaccination ({reports:,} Misreports)")
        sign_prevax = '-'
        ha = 'right'
    else:
        plt.legend(fontsize="x-small", loc="upper right")
        plt.xlabel(f"{title} Onset (Days)")
        plt.title(f"VAERS {title}s Reported After Vaccination ({reports:,} Reports)")
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

    plt.subplots_adjust(left=0.07, right=.985, top=0.96, bottom=0.07)
    plt.savefig(fname, dpi=135)


def chunk(n, chunks, lst):
    if not chunks or chunks == 1:
        return lst
    csize = len(lst) / chunks
    return(lst[int(n * csize):int((n + 1) * csize)])


def plot_vaxfreq(vax_data, args):
    print("VAXFREQ")
    reports = vax_data[REPORTS]
    vax_data = {k: v for k, v in vax_data.items() if k != REPORTS}

    pos = []
    labels = []
    frequency = []
    rows = args.n
    i = 0
    v_last = None

    # print each report to stdout
    fd_vaxfreq = open("vaxfreq.txt", "w")

    for k, v in sorted(vax_data.items(), reverse=True, key=lambda kv: kv[1]):
        if v_last is None or v_last != v:
            v_last = v
            i += 1
        pos.append(i)
        label = SYMPTOM_EXP.get(k, k)
        label = f"{label:s} #{i:d}"
        labels.append(label)
        frequency.append(v)
        print(v, label)
        fd_vaxfreq.write(f"{v} {label}\n")
        if i+1 >= rows:
            break

    fd_vaxfreq.close()

    chunks = int(round(len(labels) / args.chunksize))

    for ci in range(chunks or 1):
        pos_c = chunk(ci, chunks, pos)
        labels_c = chunk(ci, chunks, labels)
        frequency_c = chunk(ci, chunks, frequency)

        pos_c = [c - pos_c[0] for c in pos_c]

        ysize = len(frequency_c) * 0.1

        plt.figure(num=ci, figsize=(8, ysize))
        plt.rc('xtick', labelsize=8)
        plt.barh(pos_c, frequency_c, align='center')

        for p, f in zip(pos_c, frequency_c):
            plt.text(f, p + 0.25, f" {f:,d}", fontsize=6)

        plt.yticks(pos_c, labels_c, fontsize=6)
        plt.xlim(0, max(frequency) * 1.08)
        plt.ylim((max(pos_c) + .5), -0.5)
        symlist = ", ".join(args.vaxfreq)
        title = f"{reports:,d} {symlist:s} Unverified VAERS Reports By Symptom Frequency"
        plt.title(title, fontsize=11)
        plt.subplots_adjust(left=0.32, right=.985, top=0.97, bottom=0.03)
        plt.savefig("vaxfreq{0:04d}.png".format(ci + 1), dpi=300)
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot VAERS onset data.")
    parser.add_argument('-n', default=400, type=int, help="show N entries")
    parser.add_argument('--chunksize', type=int, default=100, help="Chunks have N entries each")
    parser.add_argument('--symptoms', type=str, nargs="+", help="require these symptoms")
    parser.add_argument('--vaxfreq', type=str, nargs=1, help="plot symptom frequency")
    parser.add_argument('--death', action="store_true", help="deaths only")
    parser.add_argument('--vax', nargs='+', help="count these vaccinations only")
    parser.add_argument('--prevax', action="store_true", help="show pre-vaccination reports (events before vaccination)")
    parser.add_argument('--ylog', action="store_true", help="plot Y axis in log")
    parser.add_argument('--acc', action="store_true", help="accumulate")
    parser.add_argument('stats', metavar='DATA.csv', type=str, nargs="+",
                        help='CSV files from https://vaers.hhs.gov/data/datasets.html')

    args = parser.parse_args()

    if args.vaxfreq:
        with shelve.open('vax_data_vaxfreq') as vax_data:
            if vax_data:
                print("opened cache")
            else:
                vax_data.update(parse(args.stats, args))
            plot_vaxfreq(vax_data, args)
    else:
        with shelve.open('vax_data_onset') as vax_data:
            if vax_data:
                print("opened cache")
            else:
                vax_data.update(parse(args.stats, args))
            plot_onset(vax_data, args)


if __name__ == "__main__":
    main()
