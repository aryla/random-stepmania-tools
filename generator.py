#!/usr/bin/env python3

import sys
import pysm
import random
import enum
import heapq
from heapdict import heapdict


class Vertex:
    def __init__(self, note=-1, tick=None):
        self.note = note
        self.ticks = []
        if tick is not None:
            self.ticks.append(tick)
        self._color = None
        self.hard_edges = set()
        self.soft_edges = dict()
        self.available = {0, 1, 2, 3}

    def connect(self, other, weight=0):
        if weight == 0:
            try:
                del self.soft_edges[other]
                del other.soft_edges[self]
            except KeyError:
                pass
            self.hard_edges.add(other)
            other.hard_edges.add(self)

            self.available.discard(other.color)
            other.available.discard(self.color)

        elif other not in self.hard_edges:
            self.soft_edges[other] = weight
            other.soft_edges[self] = weight

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if color is None:
            self._color = None
            self.update()
            for v in self.hard_edges:
                v.update()
        else:
            self._color = color
            for other in self.hard_edges:
                other.available.discard(color)

    def update(self):
        self.available = {0, 1, 2, 3}
        for v in self.hard_edges:
            self.available.discard(v.color)


def n_entropy(vertex):
    return -(len(vertex.hard_edges) - (4 ** len(vertex.available)))


def choose(options):
    draw = random.random() * sum(options.values())
    for o, w in options.items():
        if draw <= w:
            return o
        draw -= w


def color_graph_helper(graph):
    stack = []
    vertex, old_entropy = graph.popitem()
    stack.append((vertex, old_entropy, set(vertex.available)))

    while len(stack) > 0:
        vertex, old_entropy, available = stack.pop()

        if len(available) > 0:
            options = {}
            for color in available:
                weight = 1
                for (v, w) in vertex.soft_edges.items():
                    if v.color == color:
                        weight *= w
                options[color] = weight
            vertex.color = choose(options)
            assert vertex.color is not None
            for v in vertex.hard_edges:
                if v.color is None:
                    graph[v] = n_entropy(v)

            available.discard(vertex.color)
            stack.append((vertex, old_entropy, available))

            if len(graph) == 0:
                break

            vertex, old_entropy = graph.popitem()
            stack.append((vertex, old_entropy, set(vertex.available)))

        else:
            vertex.color = None
            for v in vertex.hard_edges:
                if v.color is None:
                    graph[v] = n_entropy(v)
            graph[vertex] = old_entropy

    if len(graph) > 0:
        raise ValueError


def color_graph(graph):
    changed = True
    while changed:
        changed = False
        for v in graph:
            if v.color is not None:
                continue
            if len(v.available) == 0:
                raise TypeError('No colors left')
            if len(v.available) == 1:
                v.color = list(v.available)[0]
                changed = True

    heap = heapdict()
    for v in graph:
        if v.color is None:
            heap[v] = n_entropy(v)

    color_graph_helper(heap)


def irows(measures):
    tick = 0
    for measure in measures:
        for row in measure.notes:
            try:
                yield (tick, row)
            except ValueError:
                pass
            finally:
                tick += 1


def get_row(notes, tick):
    measure_number = tick // 192
    try:
        measure = notes.value.measures[measure_number]
    except IndexError:
        return None
    return measure.notes[tick % 192]


def generate_from_template(template):
    left  = Vertex()
    right = Vertex()
    up    = Vertex()
    down  = Vertex()

    left.color  = 0
    up.color    = 1
    down.color  = 2
    right.color = 3

    graph = [ left, right, up, down ]

    foot = random.choice([0, 1])
    sides = [left, right]
    history = [[],[]]
    prev = -1
    series = [None] * 8
    for tick, row in irows(template.measures):
        mines = [i for i, x in enumerate(row) if x == 'M']
        notes = [i for i, x in enumerate(row) if x in '124']

        for mine in mines:
            series[mine] = None

        for note in notes:

            vertex = None

            if prev < 0:
                # first note
                # always start with a left or right note
                vertex = sides[foot]
                if note != 7:
                    series[note] = vertex

            elif note != 7 and note == prev:
                # double step
                foot = 1 - foot
                vertex = history[foot][-1]

            elif note == 0:
                # crossover
                vertex = sides[1 - foot]
                other = history[1 - foot]
                if len(other) > 0:
                    vertex.connect(other[-1])

            elif prev == 0 and len(history[foot]) > 0:
                # after crossover
                vertex = history[foot][-1]
                other = history[1 - foot]
                if len(other) > 0:
                    vertex.connect(other[-1])

            elif note == 7:
                # wild card note
                vertex = Vertex(note)
                graph.append(vertex)
                vertex.connect(sides[1 - foot])

                other = history[1 - foot]
                if len(other) > 0:
                    vertex.connect(other[-1])

                if len(history[foot]) > 0:
                    if history[foot][-1] in series:
                        vertex.connect(history[foot][-1], 0)
                    else:
                        vertex.connect(history[foot][-1], 0.25)

            else:
                # part of a series
                if series[note] is not None and \
                        series[note].ticks[-1] >= tick - 96:
                    vertex = series[note]
                else:
                    vertex = Vertex(note)
                    graph.append(vertex)
                    series[note] = vertex

                vertex.connect(sides[1 - foot])

                other = history[1 - foot]
                if len(other) > 0:
                    vertex.connect(other[-1])
                if len(history[foot]) > 0 and \
                        history[foot][-1] is not vertex:
                    vertex.connect(history[foot][-1], 0)

            vertex.ticks.append(tick)
            history[foot].append(vertex)
            prev = note
            foot = 1 - foot
        # for note in notes
    # for tick, row in irows

    color_graph(graph)

    measures = [
        pysm.Measure([['0'] * 4 for _ in range(192)])
        for _ in template.measures
    ]
    for vertex in graph:
        for tick in vertex.ticks:
            if tick >= 0:
                measures[tick // 192].notes[tick % 192][vertex.color] = '1'

    return pysm.Notes(
        'dance-single',
        'generated',
        template.level,
        template.feet,
        template.groove,
        measures)


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        data = f.read()

    simfile = pysm.loads(data)
    for h in simfile.headers:
        if h.name == pysm.Invalid:
            raise ValueError()

    templates = [
        chart.value for chart in simfile.notes
        if chart.value.credit == 'template'
    ]

    # Delete existing charts.
    for chart in simfile.notes:
        if chart.value.credit == 'generated':
            simfile.headers.remove(chart)

    # Generate new charts.
    for template in templates:
        simfile.headers.append(pysm.Header('NOTES',
            generate_from_template(template)
        ))

    new_data = str(simfile)
    with open(sys.argv[1], 'w') as f:
        f.write(new_data)
