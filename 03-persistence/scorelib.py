from enum import Enum
import re

Regex = {
    'NUMBER': r'.*?(\d+)',
    'ANYTHING_AFTER_COLON': r'.*?:(.*)',
    'COMPOSER': r'(.+?)\(([^-]*)(-{1,2}|\+|\*)([^-]*)\)',
    'Y': r'.*?(y)',
    'COMPOSITION_YEAR': r'.*?(\d{3,})',
    'VOICE': r'\s*(?:(\S+?)(-{2})(\S+?)(?:,|;)\s*){0,1}(.*)',
    'EDITOR': r'(?:(?:[^\,]+\.?)(?:\,?\s+))?(?:[^\,]+\.?)'
}

class Composition:
    def __init__(self, name = None, incipit = None, key = None, genre = None, year = None, voices = [], authors = []):
        self.name = name
        self.incipit = incipit
        self.key = key
        self.genre = genre
        self.year = year
        self.voices = voices
        self.authors = authors

    def format1(self):
        if(len(self.authors) > 0 and len(self.formatAuthors()) > 0):
            print('{}: {}'.format(Line.COMPOSER.value, self.formatAuthors()))
        if(self.name):
            print('{}: {}'.format(Line.TITLE.value, self.name))
        if(self.genre):
            print('{}: {}'.format(Line.GENRE.value, self.genre))
        if(self.key):
            print('{}: {}'.format(Line.KEY.value, self.key))
        if(self.year):
            print('{}: {}'.format(Line.COMPOSITION_YEAR.value, self.year))

    def format2(self):
        if(len(self.voices) > 0):
            i = 0
            for v in self.voices:
                if(v.name or v.range):
                    i += 1
                    print('{} {}: {}'.format(Line.VOICE.value, i, v.formatted()))

    def formatAuthors(self):
        formatted = ''
        for a in self.authors:
            formatted += a.formatted() + "; "
        return formatted[:-2]

class Edition:
    def __init__(self, composition = Composition(), authors = [], name = None):
        self.composition = composition
        self.authors = authors
        self.name = name

    def format(self):
        self.composition.format1()
        if(self.name):
            print('{}: {}'.format(Line.EDITION.value, self.name))
        if(len(self.authors) > 0):
            print('{}: {}'.format(Line.EDITOR.value, self.formatAuthors()))
        self.composition.format2()

    def formatAuthors(self):
        formatted = ''
        for a in self.authors:
            formatted += a.formatted() + ", "
        return formatted[:-2]

class Print:
    def __init__(self, edition = Edition(), print_id = -1, partiture = False):
        self.edition = edition
        self.print_id = print_id
        self.partiture = partiture

    def format(self):
        print('{}: {}'.format(Line.PRINT_NUMBER.value, self.print_id))
        self.edition.format()
        print('{}: {}'.format(Line.PARTITURE.value, 'yes' if self.partiture else 'no'))
        if(self.composition().incipit):
            print('{}: {}'.format(Line.INCIPIT.value, self.composition().incipit))
        print()

    def composition(self):
        return self.edition.composition

class Voice:
    def __init__(self, name = None, range = None):
        self.name = name
        self.range = range

    def formatted(self):
        return ('{}, '.format(self.range) if self.range else '') + (self.name if self.name else '')

class Person:
    def __init__(self, name = None, born = None, died = None):
        self.name = name
        self.born = born
        self.died = died

    def formatted(self):
        formatted = self.name
        if self.born or self.died:
            formatted += '({}--{})'.format(self.born if self.born else '', self.died if self.died else '')
        return formatted

class Line(Enum):
    PRINT_NUMBER = 'Print Number'
    COMPOSER = 'Composer'
    TITLE = 'Title'
    GENRE = 'Genre'
    KEY = 'Key'
    COMPOSITION_YEAR = 'Composition Year'
    PUBLICATION_YEAR = 'Publication Year'
    EDITION = 'Edition'
    EDITOR = 'Editor'
    VOICE = 'Voice'
    PARTITURE = 'Partiture'
    INCIPIT = 'Incipit'

#from here on now expect mess and ugliness, 'cause supposedly those things belong here *logically*

def parseSimple(line, regex, group = 1, defval = None, parseint = False):
    r = re.compile(Regex[regex])
    m = r.match(line)
    if m:
        m = m.group(group)
        return m.strip() if not parseint else int(m.strip())
    return defval

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def parseComposer(line):
    if line == None:
        return []
    authors = []
    for composer in line.split(';'):
        composer = composer.strip()
        person = Person()
        r = re.compile(Regex['COMPOSER'])
        m = r.match(composer)
        if m:
            person.name = m.group(1)
            if m.group(2) and isInt(m.group(2)):
                person.born = int(m.group(2))
            if m.group(4) and isInt(m.group(4)):
                if m.group(3) == '*':
                    person.born = int(m.group(4))
                else:
                    person.died = int(m.group(4))
        else:
            person.name = composer
        authors.append(person)
    return authors

def parseEdition(name):
    if name == None:
        return ''
    return name

def parseEditor(line):
    editors = []
    if line == None:
        return editors
    r = re.compile(Regex['EDITOR'])
    m = r.findall(line)
    for name in m:
        p = Person()
        p.name = name.strip()
        editors.append(p)
    return editors

def parseVoice(line):
    v = Voice()
    if line == None:
        return v
    r = re.compile(Regex['VOICE'])
    m = r.match(line.strip())
    if m:
        v.name = m.group(4)
        range = ''
        if m.group(1):
            range += m.group(1)
        range += '--'
        if m.group(3):
            range += m.group(3)
        v.range = range if len(range) > 2 else None
    return v

def parsePartiture(line):
    return True if parseSimple(line, 'Y') else False

def starts(line, linetype):
    return line.lower().startswith(linetype.value.lower())

def parse(_temp, line):
    if starts(line, Line.PRINT_NUMBER):
        _temp['print'].print_id = parseSimple(line, 'NUMBER', parseint = True)
    elif starts(line, Line.COMPOSER):
        _temp['composition'].authors = parseComposer(parseSimple(line, 'ANYTHING_AFTER_COLON'))
    elif starts(line, Line.TITLE):
        _temp['composition'].name = parseSimple(line, 'ANYTHING_AFTER_COLON')
    elif starts(line, Line.GENRE):
        _temp['composition'].genre = parseSimple(line, 'ANYTHING_AFTER_COLON')
    elif starts(line, Line.KEY):
        _temp['composition'].key = parseSimple(line, 'ANYTHING_AFTER_COLON')
    elif starts(line, Line.COMPOSITION_YEAR):
        _temp['composition'].year = parseSimple(line, 'COMPOSITION_YEAR', parseint = True)
    elif starts(line, Line.PUBLICATION_YEAR):
        pass
    elif starts(line, Line.EDITION):
        _temp['edition'].name = parseSimple(line, 'ANYTHING_AFTER_COLON')
    elif starts(line, Line.EDITOR):
        _temp['edition'].authors = parseEditor(parseSimple(line, 'ANYTHING_AFTER_COLON'))
    elif starts(line, Line.VOICE):
        _temp['voices'].append(parseVoice(parseSimple(line, 'ANYTHING_AFTER_COLON')))
    elif starts(line, Line.PARTITURE):
        _temp['print'].partiture = parsePartiture(line)
    elif starts(line, Line.INCIPIT):
        _temp['composition'].incipit = parseSimple(line, 'ANYTHING_AFTER_COLON')

def process(block):
    _print = Print()
    composition = Composition()
    edition = Edition()
    voices = []
    _temp = {'print': _print, 'composition': composition, 'edition': edition, 'voices': voices}

    for line in block:
        parse(_temp, line)

    composition.voices = voices
    edition.composition = composition
    _print.edition = edition

    return _print

def load(filename):
    prints = []
    blocks = []
    reading = []

    with open(filename, errors='ignore') as file:
        for line in file:
            if line != '\n':
                reading.append(line)
            else:
                blocks.append(reading)
                reading = []
        blocks.append(reading)

    for block in blocks:
        prints.append(process(block))

    return list(filter(lambda y: y.print_id >= 0, sorted(prints, key = lambda x: x.print_id)))