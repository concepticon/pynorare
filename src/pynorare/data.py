from cldfcatalog import Config 
from csvw.dsv import UnicodeDictReader, UnicodeReader
from collections import defaultdict
from pyconcepticon import Concepticon

import xlrd
from urllib.request import urlretrieve
from tempfile import TemporaryDirectory
from pathlib import Path
from zipfile import ZipFile
from csvw.metadata import TableGroup

from pynorare import log

import attr

def get_mappings():

    # get mappings etc.
    repos = Config.from_file().get_clone('concepticon')
    concepticon = Concepticon(repos)
    paths = {p.stem.split('-')[1]: p for p in repos.joinpath(
        'mappings').glob('map-*.tsv')}
    mappings = {} 
    for language, path in paths.items(): 
        mappings[language] = defaultdict(set) 
        with UnicodeDictReader(path, delimiter='\t') as reader: 
            for line in reader: 
                gloss = line['GLOSS'].split('///')[1]
                oc = concepticon.conceptsets[line['ID']].ontological_category
                mappings[language][gloss].add( 
                    (line['ID'], int(line['PRIORITY']), oc))
    for language, path in paths.items():
        for k, v in mappings[language].items():
            mappings[language][k] = sorted(v, key=lambda x: x[1], reverse=True)
    return mappings, concepticon


def get_excel(path, sheet_index, dicts=False):
    xlfile = xlrd.open_workbook(Path('raw').joinpath(path).as_posix())
    sheet = xlfile.sheet_by_index(sheet_index)
    sheet = [sheet.row_values(i) for i in range(0, sheet.nrows)]
    if dicts:
        sheet = [dict(zip(sheet[0], row)) for row in sheet[1:]]
    log.loaded(path)
    return sheet


def get_csv(path, delimiter="\t", dicts=True, extract=False):
    sheet = []
    path = Path('raw').joinpath(path).as_posix()
    if dicts:
        with UnicodeDictReader(path, delimiter=delimiter) as reader:
            for line in reader:
                sheet += [line]
    else:
        with UnicodeReader(path, delimiter=delimiter) as reader:
            for line in reader:
                sheet += [line]
    log.loaded(path)
    return sheet


def download_file(url, target):
    path = Path('raw').joinpath(target).as_posix()
    urlretrieve(url, path)
    log.download(url)


def download_zip(url, target, filename):
    download_file(url, target)
    path = Path('raw').joinpath(target).as_posix()
    with open(path, 'rb') as f:
        with ZipFile(f) as zf:
            zf.extract(filename, path='raw')


@attr.s
class NormDataSet:
    mapped = defaultdict(list)
    mappings, concepticon = get_mappings()
    id = ""

    def validate(self):
        tbg = TableGroup.from_file(self.id+'.tsv-metadata.json')
        mappings = list(tbg.tabledict[self.id+'.tsv'])
        if not self.mapped:
            self.map()
        if len(self.mapped) == len(mappings):
            log.info('metadata file can be loaded')

        if 'CONCEPTICON_ID' in mappings[0] and 'CONCEPTICON_GLOSS' in mappings[0] and 'LINE_IN_SOURCE' in mappings[0]:
            log.info('concepticon data present in data')

    def map(self):
        log.warning("Function MAP is not defined")
        return 

    def download(self):
        return

    def extract_data(
            self, 
            dicts,
            namespace,
            header,
            gloss='ENGLISH',
            language='en'
            ):
        mapped = defaultdict(list)
        for i, row in enumerate(dicts):
            new_row = {b: c(row[a]) for a, b, c in namespace}
            if not 'LINE_IN_SOURCE' in new_row:
                new_row['LINE_IN_SOURCE'] = str(i+1)
            if new_row[gloss] in self.mappings[language]:
                match, priority, pos = self.mappings[language][new_row[gloss]][0]
                new_row['CONCEPTICON_ID'] = str(match)
                new_row['CONCEPTICON_GLOSS'] = \
                        self.concepticon.conceptsets[match].gloss
                new_row['_PRIORITY'] = priority
                mapped[match] += [new_row]
        table = []
        for key, rows in sorted(mapped.items(), key=lambda x: x[0]):
            row = sorted(
                    rows, 
                    key=lambda x: (x['_PRIORITY']))[0]
            table += [[row[h] for h in header]]
        self.mapped = mapped
        self.writefile(header, table)

    def run(self, args):
        if 'download' in args:
            self.download()
        if 'map' in args:
            self.map()
            log.matches(len(self.mapped))
        if 'validate' in args:
            self.validate()
    
    def writefile(self, header, table):
        with open(self.id+'.tsv', 'w') as f:
            f.write('\t'.join(header)+'\n')
            for line in table:
                if not len(line) == len(header):
                    raise ValueError(
                        "header and lines in table are of different length")
                f.write('\t'.join(line)+'\n')
                
        log.written(self.id+'.tsv')

