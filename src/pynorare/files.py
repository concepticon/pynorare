import collections

import requests
from cldfcatalog import Config
from pyconcepticon import Concepticon
import xlrd
import openpyxl

from pynorare.util import read_wellformed_tsv_or_die


def get_mappings(concepticon=None):
    concepticon = concepticon or Concepticon(Config.from_file().get_clone('concepticon'))
    paths = {p.stem.split('-')[1]: p
             for p in concepticon.repos.joinpath('mappings').glob('map-*.tsv')}
    mappings = {}
    for language, path in paths.items():
        mappings[language] = collections.defaultdict(set)
        for line in read_wellformed_tsv_or_die(path):
            gloss = line['GLOSS'].split('///')[1]
            oc = concepticon.conceptsets[line['ID']].ontological_category
            mappings[language][gloss].add((line['ID'], int(line['PRIORITY']), oc))
    for language, path in paths.items():
        for k, v in mappings[language].items():
            # We sort concepticon matches for a given gloss by descending priority and ascending
            # Concepticon ID.
            mappings[language][k] = sorted(v, key=lambda x: (x[1], -int(x[0])), reverse=True)
    return mappings, concepticon


def get_excel(path, sheet_index, dicts=False):
    if path.suffix == ".xlsx":
        xlfile = openpyxl.load_workbook(str(path), data_only=True)
        sheet = [[cell.value for cell in r] for r in xlfile[xlfile.sheetnames[sheet_index]].rows]
    else:
        sheet = xlrd.open_workbook(str(path)).sheet_by_index(sheet_index)
        sheet = [sheet.row_values(i) for i in range(0, sheet.nrows)]
    return [dict(zip(sheet[0], row)) for row in sheet[1:]] if dicts else sheet


def download_file(url, path):  # pragma: no cover
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return path
