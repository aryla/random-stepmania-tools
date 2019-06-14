#!/usr/bin/env python3

import sys
import pysm


def get_row(chart, tick):
    measure_number = tick // 192
    try:
        measure = chart.measures[measure_number]
    except IndexError:
        return None
    return measure.notes[tick % 192]


def irows(chart):
    for measure in chart.measures:
        for tick in range(192):
            yield measure.notes[tick]


def generate_practice(template, player):
    if player == 'holds':
        to_mines = '4'
    else:
        to_mines = '2'

    measures = [
        pysm.Measure([list(t_row) for t_row in t_measure.notes])
        for t_measure in template.measures
    ]
    result = pysm.Notes(
        'dance-double',
        'Practice ({})'.format(player[0].upper() + player[1:]),
        'Edit',
        str(int(template.feet) - 1),
        template.groove,
        measures)

    for tick, row in enumerate(irows(template)):
        for col, note in enumerate(row):
            if note != to_mines:
                continue

            get_row(result, tick)[col] = 'M'

            tail = 0
            while get_row(result, tick + tail)[col] != '3':
                if tail > 0 and tail % 48 == 0:
                    get_row(result, tick + tail)[col] = 'M'
                tail += 1
            get_row(result, tick + tail)[col] = '0'

    return result


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        data = f.read()

    simfile = pysm.loads(data)
    for h in simfile.headers:
        if h.name == pysm.Invalid:
            raise ValueError()

    for chart in simfile.notes:
        if chart.value.game != 'dance-double':
            continue

        if 'practice' in chart.value.credit.lower() and chart.value.level == 'Edit':
            # Delete existing charts.
            simfile.headers.remove(chart)

        else:
            simfile.headers.append(pysm.Header('NOTES',
                generate_practice(chart.value, 'holds')
            ))
            simfile.headers.append(pysm.Header('NOTES',
                generate_practice(chart.value, 'rolls')
            ))

    new_data = str(simfile)
    with open(sys.argv[1], 'w') as f:
        f.write(new_data)
