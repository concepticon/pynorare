from pathlib import Path
from csvw.metadata import TableGroup
from csvw.dsv import UnicodeDictReader
from tqdm import tqdm
from pynorare import log
import attr
from collections import OrderedDict, defaultdict


@attr.s
class Column(object):
    dataset = attr.ib()
    name = attr.ib()
    structure = attr.ib()
    type = attr.ib()
    norare = attr.ib()
    rating = attr.ib()
    nameinsource = attr.ib()
    note = attr.ib()


@attr.s
class ConceptSetMeta(object):
    id = attr.ib()
    author = attr.ib()
    year = attr.ib()
    tags = attr.ib(repr=False, converter=lambda x: x.split(','))
    source_language = attr.ib(repr=False)
    target_language = attr.ib(repr=False)
    url = attr.ib(repr=False)
    refs = attr.ib(repr=False)
    note = attr.ib(repr=False)
    alias = attr.ib(repr=False)
    norare = attr.ib(default=None, repr=False)

    @property
    def concepts(self):
        tbg = TableGroup.from_file(
                self.norare.repos.joinpath(
                    'concept_set_meta',
                    self.id,
                    self.id+'.tsv-metadata.json').as_posix())
        concepts = OrderedDict()
        for row in tbg.tabledict[self.id+'.tsv']:
            concepts[row['CONCEPTICON_ID']] = OrderedDict({k.lower(): v for k,
                v in row.items()})
        return concepts
    
    @property
    def columns(self):
        tbg = TableGroup.from_file(
                self.norare.repos.joinpath(
                    'concept_set_meta',
                    self.id,
                    self.id+'.tsv-metadata.json').as_posix())
        columns = OrderedDict({c.name.lower(): {'nameinsource': str(c.titles) if c.titles
            else ''} for c in
                tbg.tabledict[self.id+'.tsv'].tableSchema.columns})

        for c in tbg.tabledict[self.id+'.tsv'].tableSchema.columns:
            params = {
                    'dataset': self.id,
                    'name': c.name.lower(),
                    'nameinsource': str(c.titles) if c.titles else '',
                    'structure': '',
                    'norare': '',
                    'type': '',
                    'rating': '',
                    'note': '',
                    }
            columns[c.name.lower()] = Column(
                    dataset=self.id,
                    name=c.name.lower(),
                    structure=self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'structure': ''})['structure'],
                    type=self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'type': ''})['type'],
                    norare=self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'norare': ''})['norare'],
                    rating=self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'rating': ''})['rating'],
                    note=self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'note': ''})['note'],
                    nameinsource=str(c.titles) if c.titles else ''
                    )

        return columns


@attr.s
class NoRaRe():
    repos = attr.ib(default=None, converter=Path)
    datasets = attr.ib(default=OrderedDict())

    def __attrs_post_init__(self):
        


        with UnicodeDictReader(self.repos.joinpath('concept_set_meta.tsv'),
                delimiter='\t') as reader:
            for row in reader:
                row['norare'] = self
                self.datasets[row['ID']] = ConceptSetMeta(
                        **{k.lower(): v for k, v in row.items()})
        self.annotations = defaultdict(lambda : OrderedDict())
        with UnicodeDictReader(self.repos.joinpath('norare.tsv'), delimiter='\t') as reader:
            for row in reader:
                self.annotations[row['DATASET']][row['NAME'].lower()] = {
                        k.lower(): row[k] for k in ['DATASET', 'NAME', 'STRUCTURE',
                            'TYPE', 'NORARE', 'RATING', 'SOURCE', 'NOTE']}

    def __iter__(self):
        return iter(self.norms)
