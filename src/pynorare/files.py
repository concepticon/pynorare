import zipfile
import collections
from urllib.request import urlretrieve

from cldfcatalog import Config
from csvw.dsv import reader
from pyconcepticon import Concepticon

import xlrd


def get_mappings(concepticon=None):
    concepticon = concepticon or Concepticon(Config.from_file().get_clone('concepticon'))
    paths = {p.stem.split('-')[1]: p
             for p in concepticon.repos.joinpath('mappings').glob('map-*.tsv')}
    mappings = {}
    for language, path in paths.items():
        mappings[language] = collections.defaultdict(set)
        for line in reader(path, delimiter='\t', dicts=True):
            gloss = line['GLOSS'].split('///')[1]
            oc = concepticon.conceptsets[line['ID']].ontological_category
            mappings[language][gloss].add((line['ID'], int(line['PRIORITY']), oc))
    for language, path in paths.items():
        for k, v in mappings[language].items():
            # We sort concepticon matches for a given gloss by descending priority and ascending
            # Concepticon ID.
            mappings[language][k] = sorted(
                v, key=lambda x: (x[1], -int(x[0])), reverse=True)
    return mappings, concepticon


def get_excel(path, sheet_index, dicts=False):
    xlfile = xlrd.open_workbook(str(path))
    sheet = xlfile.sheet_by_index(sheet_index)
    sheet = [sheet.row_values(i) for i in range(0, sheet.nrows)]
    return [dict(zip(sheet[0], row)) for row in sheet[1:]] if dicts else sheet


def download_archive(url, target, filename, path, cls=zipfile.ZipFile):
    urlretrieve(url, str(target))
    with open(str(target), 'rb') as f:
        with cls(f) as archive:
            archive.extract(filename, path=str(path))
