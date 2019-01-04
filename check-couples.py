#!/usr/bin/env python3

import sys
import pysm


def get_arrow(note, col):
    if note == '1':
        return '←↓↑→←↓↑→'[col]
    elif note == '2':
        return '⇐⇓⇑⇒⇐⇓⇑⇒'[col]
    elif note == '4':
        return '↞↡↟↠↞↡↟↠'[col]

    return {
        'M': '✳',
    }.get(note, ' ')


def check_chart(chart):
    holds = []
    rolls = []

    for measure_number, measure in enumerate(chart.value.measures):
        errors = set()

        for tick, row in enumerate(measure.notes):
            def check_row(char, other):
                for col, note in enumerate(row):
                    if note == char:
                        for notes in other:
                            if col in notes:
                                yield (tick, col)

            def add_steps(char, player):
                mines = {col for col, note in enumerate(row) if note == 'M'}
                steps = {col for col, note in enumerate(row) if note == char}
                if len(steps) > 1:
                    player.clear()
                    player.append(steps)
                    player.append(set())
                elif len(steps) == 1:
                    if len(player) == 0 or player[-1] != steps:
                        if len(player) > 1:
                            player.pop(0)
                        player.append(steps)

                for foot in player:
                    foot.difference_update(mines)

            add_steps('2', holds)
            add_steps('4', rolls)

            errors.update(check_row('2', rolls))
            errors.update(check_row('4', holds))

        if len(errors) > 0:
            print('--------- {0:^ 4} ---------'.format(measure_number))
            measure = chart.value.measures[measure_number]
            for tick in range(0, 192, measure.row_dist):
                for col, note in enumerate(measure.notes[tick]):
                    if (tick, col) in errors:
                        fmt = '[{0}]'
                    else:
                        fmt = ' {0} '
                    print(fmt.format(get_arrow(note, col)), end='')
                print()
            print()


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        data = f.read()

    simfile = pysm.loads(data)
    for h in simfile.headers:
        if h.name == pysm.Invalid:
            raise ValueError()

    for chart in simfile.notes:
        check_chart(chart)
