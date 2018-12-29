from collections import namedtuple
import math
import re
import sys
import traceback


class ParseError(ValueError):
    pass


class Header:
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value

    def __str__(self):
        return '#' + self.name + ':' + str(self.value) + ';'

    def __repr__(self):
        return '{}(name={}, value={})'.format(
            self.__class__.__name__,
            repr(self.name),
            repr(self.value),
        )


class Comment(Header):
    def __init__(self, data):
        super().__init__(name=Comment, value=data)

    def __str__(self):
        return self.value


class Invalid(Header):
    def __init__(self, data):
        super().__init__(name=Invalid, value=data)

    def __str__(self):
        return self.value


class Speeds:
    def __init__(self, speeds, original_str=None):
        super().__init__()
        if original_str is not None:
            self._original_str = original_str
            self._original_speeds = speeds
        else:
            self._original_str = None
            self._original_speeds = None
        self.speeds = speeds

    def __str__(self):
        if self.speeds == self._original_speeds:
            return self._original_str

        result = '\n,'.join((
            '{:.03f}={:.03f}'.format(time, duration)
            for time, duration in self.speeds
        ))
        if len(self.speeds) > 1:
            result += '\n'
        return result


class Bpms(Speeds):
    pass


class Stops(Speeds):
    pass


class Measure:
    def __init__(self, notes, original_str=None):
        super().__init__()
        if original_str is not None:
            self._original_str = original_str
            self._original_notes = [
                list(row) for row in notes
            ]
        else:
            self._original_str = None
            self._original_notes = None
        self.notes = notes

    @property
    def row_dist(self):
        row_dist = 48
        for tick in range(192):
            for note in self.notes[tick]:
                if note != '0':
                    row_dist = math.gcd(tick, row_dist)
        return row_dist


    def __str__(self):
        if self.notes == self._original_notes:
            return self._original_str
        return '\n' + '\n'.join((
            ''.join(self.notes[tick])
            for tick in range(0, 192, self.row_dist)
        )) + '\n'


class Notes:

    METADATA = ['game', 'credit', 'level', 'feet', 'groove']

    def __init__(self, game, credit, level, feet, groove, measures):
        super().__init__()

        self._meta = {}
        self._original_meta = {}
        self._original_meta_clean = {}
        for key in self.METADATA:
            self._init_meta(key, locals()[key])

        self.measures = measures

    def _init_meta(self, key, value):
        clean = value.strip()
        self._meta[key] = clean
        self._original_meta_clean[key] = clean
        self._original_meta[key] = value

    def _str_meta(self, key):
        if self._meta[key] == self._original_meta_clean[key]:
            return self._original_meta[key]
        else:
            return '\n     ' + self._meta[key]

    def __str__(self):
        return ':'.join((
            self._str_meta(key) for key in self.METADATA
        )) + ':' + ','.join((
            str(m) for m in self.measures
        ))

    def __getattr__(self, key):
        if key in self.METADATA:
            return self._meta[key]
        raise AttributeError('%r object has no attribute %r'.format(type(self).__name__, key))


class Simfile:

    METADATA = {
        'TITLE',
        'SUBTITLE',
        'ARTIST',
        'TITLETRANSLIT',
        'SUBTITLETRANSLIT',
        'ARTISTTRANSLIT',
        'GENRE',
        'CREDIT',
        'MUSIC',
        'BANNER',
        'BACKGROUND',
        'CDTITLE',
        'SAMPLESTART',
        'SAMPLELENGTH',
        'SELECTABLE',
        'OFFSET',
        'BPMS',
        'STOPS',
        'BGCHANGES',
        'FGCHANGES',
    }

    def __init__(self, headers):
        super().__init__()

        self.notes = []
        self.headers = headers

        for key in self.METADATA:
            setattr(self, key.lower(), None)
        for h in headers:
            if h.name in self.METADATA:
                setattr(self, h.name.lower(), h)
            elif h.name == 'NOTES':
                self.notes.append(h)

    def __str__(self):
        return ''.join((
            str(h) for h in self.headers
        ))


def parse_speeds(data):
    speeds = []

    for speed_str in data.split(','):
        try:
            time_str, value_str = speed_str.strip().split('=')
            time = float(time_str)
            value = float(value_str)
            speeds.append((time, value))
        except (ValueError, TypeError):
            raise ParseError()

    return speeds


def parse_bpms(data):
    try:
        bpms = parse_speeds(data)
    except ParseError:
        return Invalid(data)
    else:
        return Bpms(bpms, data)


def parse_measure(data, num_columns):
    notes_str = re.sub('(\s|//.*)', '', data)
    if len(notes_str) % num_columns != 0:
        raise ParseError()

    timesig = len(notes_str) // num_columns
    if timesig % 4 != 0 or 192 % timesig != 0:
        raise ParseError()

    notes = [
        ['0'] * num_columns
        for _ in range(192)
    ]
    for beat in range(timesig):
        tick = beat * (192 // timesig)
        for c in range(num_columns):
            notes[tick][c] = notes_str[beat * num_columns + c]

    return Measure(notes, data)


def get_game_columns(game):
    return {
        'dance-double': 8,
        'dance-single': 4,
    }[game]


def parse_notes(data):
    try:
        colon = data.rindex(':')
    except ValueError:
        raise ParseError

    try:
        game, credit, level, feet, groove = data[:colon].split(':')
    except ValueError:
        raise ParseError

    notedata = data[colon+1:]

    try:
        columns = get_game_columns(game.strip())
    except KeyError:
        match = re.search('^\s*(\d+)\s*$', notedata, re.MULTILINE)
        if match is None:
            raise ParseError()
        columns = len(match.group(1))

    def repl(match):
        return ' ' * len(m.group(0))
    clean = re.sub('//.*$', repl, notedata, re.MULTILINE)
    assert len(clean) == len(notedata)

    measures = []
    pos = 0
    while pos < len(notedata):
        try:
            end = clean.index(',', pos)
        except ValueError:
            end = len(notedata)

        measures.append(parse_measure(notedata[pos:end], columns))
        pos = end + 1

    return Notes(game, credit, level, feet, groove, measures)


def parse_stops(data):
    try:
        stops = parse_speeds(data)
    except ParseError:
        return Invalid(data)
    else:
        return Stops(stops, data)


def parse_header(data, start):
    assert(data[start] == '#')

    end = len(data) - 1
    try:
        try:
            end = data.index(';', start)
        except ValueError:
            raise ParseError()

        try:
            colon = data.index(':', start, end)
        except ValueError:
            raise ParseError()

        name = data[start+1:colon]
        value = data[colon+1:end]
        if name == 'BPMS':
            value = parse_bpms(value)
        elif name == 'NOTES':
            value = parse_notes(value)
        elif name == 'STOPS':
            value = parse_stops(value)

    except ParseError:
        print(traceback.format_exc(), file=sys.stderr)
        return Invalid(data[start:(end + 1)]), end + 1

    else:
        return Header(name=name, value=value), end + 1


def parse_comment(data, start):
    pos = start
    while True:
        try:
            pos = data.index('\n', pos) + 1
        except ValueError:
            return Comment(data=data, start=start, end=len(data)), len(data)

        if pos >= len(data) or data[pos] == '#':
            return Comment(data[start:pos]), pos


def loads(data):
    headers = []

    pos = 0
    while pos < len(data):
        if data[pos] == '#':
            h, pos = parse_header(data, pos)
            headers.append(h)
        else:
            c, pos = parse_comment(data, pos)
            headers.append(c)

    return Simfile(headers)
