import attr
from csvw.metadata import TableGroup
from collections import defaultdict
from pathlib import Path

from pynorare.files import (
        get_mappings, get_excel, get_csv, download_file, download_zip
        )
from pynorare import log
from pynorare.types import types


@attr.s
class NormDataSet:
    repos = attr.ib(default=Path('.'))
    mapped = defaultdict(list)
    mappings, concepticon = get_mappings()
    id = ""

    @property
    def raw_dir(self):
        return self.repos.joinpath(
                'concept_set_meta',
                self.id,
                'raw')

    @property
    def types(self):
        return types()

    @property
    def dir(self):
        return self.repos.joinpath(
                'concept_set_meta',
                self.id)

    def validate(self):
        tbg = TableGroup.from_file(
                self.dir.joinpath(self.id+'.tsv-metadata.json').as_posix())
        mappings = list(tbg.tabledict[self.id+'.tsv'])
        if not self.mapped:
            self.map(write_file=False)
        if len(self.mapped) == len(mappings):
            log.info('metadata file can be loaded')

        if 'CONCEPTICON_ID' in mappings[0] and 'CONCEPTICON_GLOSS' in mappings[0] and 'LINE_IN_SOURCE' in mappings[0]:
            log.info('concepticon data present in data')

    def map(self, write_file=True):
        log.warning("Function MAP is not defined")
        return 

    def download(self):
        log.warning("Function DOWNLOAD is not defined")
        return

    def download_zip(self, url, target, filename):
        download_zip(
                url,
                self.raw_dir.joinpath(target).as_posix(),
                filename,
                self.raw_dir.as_posix()
                )
        log.download(url)

    def download_file(self, url, target):
        download_file(
                url,
                self.raw_dir.joinpath(target).as_posix())
        log.download(url)

    def get_csv(self, path, delimiter="\t", dicts=True, coding="utf-8"):
        sheet = get_csv(
                self.raw_dir.joinpath(path).as_posix(),
                delimiter,
                dicts,
                coding)
        log.info('loaded data {0}'.format(path))
        return sheet

    @property
    def table(self):
        return TableGroup.from_file(
                    self.dir.joinpath(
                        self.id+'.tsv-metadata.json')
                    ).tabledict[self.id+'.tsv']

    @property
    def columns(self):
        return self.table.tableSchema.columns

    def get_excel(self, path, sidx, dicts=True):
        sheet = get_excel(self.raw_dir.joinpath(path).as_posix(), 
                sidx,
                dicts)
        log.info('loaded data {0}'.format(path))
        return sheet
    
    def extract_data(
            self, 
            dicts,
            namespace=False,
            header=False,
            gloss='ENGLISH',
            language='en',
            write_file=True,
            ):

        # if namespace is missing, retrieve it from the metadata file
        if not namespace:
            namespace, header = [], []
            for col in self.columns:
                header += [col.name]
                if col.titles:
                    namespace += [(
                        str(col.titles), 
                        str(col.name), 
                        self.types.get(col.datatype.base, str)
                            )]

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
        self._header = header
        self._table = table
        if write_file:
            self.writefile()

    def run(self, args):
        if 'download' in args:
            self.download()
        if 'map' in args:
            self.map()
            log.matches(len(self.mapped))
        if 'validate' in args:
            self.validate()
    
    def writefile(self):
        with open(self.dir.joinpath(self.id+'.tsv').as_posix(), 'w') as f:
            f.write('\t'.join(self._header)+'\n')
            for line in self._table:
                if not len(line) == len(self._header):
                    raise ValueError(
                        "header and lines in table are of different length")
                f.write('\t'.join(line)+'\n')
        log.written(self.id+'.tsv')

