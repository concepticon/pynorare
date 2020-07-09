import inspect
import pathlib
import importlib.machinery
import collections
from urllib.request import urlretrieve

from csvw.metadata import TableGroup
from csvw.dsv import reader

from pynorare.files import get_mappings, get_excel, download_archive
from pynorare import log

__all__ = ['NormDataSet', 'get_dataset_cls']


def get_dataset_cls(dsdir, dsid=None):
    dsid = dsid or dsdir.name
    mod = importlib.machinery.SourceFileLoader(
        'norare.{}'.format(dsid.replace('-', '_')), str(dsdir / 'map.py')).load_module()
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        print(_, cls)
        if issubclass(cls, NormDataSet):
            return cls


class NormDataSet:
    id = ""

    def __init__(self, repos=pathlib.Path('.'), concepticon=None, mappings=None):
        self.repos = repos
        self.mapped = collections.defaultdict(list)
        if not mappings:  # pragma: no cover
            mappings, concepticon = get_mappings(concepticon)
        self.mappings, self.concepticon = mappings, concepticon
        self.dir = self.repos / 'concept_set_meta' / self.id
        self.raw_dir = self.dir / 'raw'
        if not self.raw_dir.exists():
            self.raw_dir.mkdir()
        self.fname = self.id + '.tsv'

    @property
    def tablegroup(self):
        return TableGroup.from_file(self.dir.joinpath(self.fname + '-metadata.json'))

    @property
    def table(self):
        return self.tablegroup.tabledict[self.fname]

    @property
    def columns(self):
        return self.table.tableSchema.columns

    def validate(self):
        mappings = list(self.table)
        if mappings:
            log.info('metadata file can be loaded')

        if 'CONCEPTICON_ID' in mappings[0] and \
                'CONCEPTICON_GLOSS' in mappings[0] and \
                'LINE_IN_SOURCE' in mappings[0]:
            log.info('concepticon data present in data')

    def map(self):  # pragma: no cover
        log.warning("Function MAP is not defined")

    def download(self):  # pragma: no cover
        log.warning("Function DOWNLOAD is not defined")

    def download_zip(self, url, target, filename):
        download_archive(url, self.raw_dir.joinpath(target), filename, self.raw_dir)
        log.download(url)

    def download_file(self, url, target):
        urlretrieve(url, str(self.raw_dir / target))
        log.download(url)

    def get_csv(self, path, delimiter="\t", dicts=True, coding="utf-8"):
        log.info('load data from {0}'.format(path))
        return list(reader(self.raw_dir / path, delimiter=delimiter, dicts=dicts, encoding=coding))

    def get_excel(self, path, sidx, dicts=True):
        sheet = get_excel(self.raw_dir.joinpath(path), sidx, dicts)
        log.info('loaded data {0}'.format(path))
        return sheet
    
    def extract_data(self,
                     dicts,
                     gloss='ENGLISH',
                     language='en',
                     pos=False,
                     pos_mapper=False,
                     pos_name='POS'):
        pos_mapper = pos_mapper or {}

        rename = {str(c.titles): c.name for c in self.columns if c.titles}
        mapped = collections.defaultdict(list)  # (conceptset ID, list of rows with matching glosses)

        for i, row in enumerate(dicts, start=1):
            new_row = {rename.get(k, k): v for k, v in row.items()}
            new_row.setdefault('LINE_IN_SOURCE', i)
            mappings = self.mappings[language].get(new_row[gloss])
            if mappings:
                match, priority = None, None
                if pos:
                    for match, priority, pos_ in reversed(mappings):
                        if pos_ == pos_mapper.get(new_row[pos_name], new_row[pos_name]) and match:
                            break
                else:
                    match, priority, pos_ = mappings[0]

                if match:
                    new_row['CONCEPTICON_ID'] = str(match)
                    new_row['CONCEPTICON_GLOSS'] = self.concepticon.conceptsets[match].gloss
                    new_row['_PRIORITY'] = priority
                    mapped[match].append(new_row)

        table = []
        for key, rows in sorted(mapped.items(), key=lambda x: x[0]):
            # We choose one representative gloss in the raw data for each conceptset ID, selecting
            # by higher priority and lower line number in the raw data.
            table.append(sorted(rows, key=lambda x: (x['_PRIORITY'], x['LINE_IN_SOURCE']))[0])

        self.mapped = mapped
        self.table.write(table, base=self.dir)

    def run(self, args):
        if 'download' in args:
            self.download()
        if 'map' in args:
            self.map()
            log.matches(len(self.mapped))
        if 'validate' in args:
            self.validate()
