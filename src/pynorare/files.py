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
    xlfile = xlrd.open_workbook(path)
    sheet = xlfile.sheet_by_index(sheet_index)
    sheet = [sheet.row_values(i) for i in range(0, sheet.nrows)]
    if dicts:
        sheet = [dict(zip(sheet[0], row)) for row in sheet[1:]]
    log.loaded(path)
    return sheet


def get_csv(path, delimiter="\t", dicts=True, coding='utf-8'):
    sheet = []
    if dicts:
        with UnicodeDictReader(path, delimiter=delimiter, encoding=coding) as reader:
            for line in reader:
                sheet += [line]
    else:
        with UnicodeReader(path, delimiter=delimiter, encoding=coding) as reader:
            for line in reader:
                sheet += [line]
    log.loaded(path)
    return sheet


def download_file(url, target):
    urlretrieve(url, target)


def download_zip(url, target, filename, path):
    download_file(url, target)
    with open(target, 'rb') as f:
        with ZipFile(f) as zf:
            zf.extract(filename, path=path)



