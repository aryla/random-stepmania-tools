#!/usr/bin/env python3

import sys
import pysm


def get_row(notes, tick):
    measure_number = tick // 192
    try:
        measure = notes.value.measures[measure_number]
    except IndexError:
        return None
    return measure.notes[tick % 192]


def irows(notes):
    for measure in notes.value.measures:
        for tick in range(192):
            yield measure.notes[tick]


def fix_chart(chart):
    for tick, row in enumerate(irows(chart)):
        for col, note in enumerate(row):
            if note != '1':
                continue

            row[col] = '4'

            next_note = 0
            for i in range(1, 16):
                next_row = get_row(chart, tick + i)
                if next_row is None or next_row[col] != '0':
                    next_note = i
                    break
            else:
                next_note = 16

            assert next_note >= 2

            if next_note >= 16:
                tail = 12
            elif next_note >= 10:
                tail = 6
            elif next_note >= 8:
                tail = 4
            elif next_note >= 6:
                tail = 3
            elif next_note >= 4:
                tail = 2
            else:
                tail = 1

            get_row(chart, tick + tail)[col] = '3'


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        data = f.read()

    simfile = pysm.loads(data)
    for h in simfile.headers:
        if h.name == pysm.Invalid:
            raise ValueError()

    for chart in simfile.notes:
        fix_chart(chart)
    print(simfile, end='')
