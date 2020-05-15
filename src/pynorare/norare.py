from pathlib import Path
from csvw.metadata import TableGroup
from csvw.dsv import UnicodeDictReader
from tqdm import tqdm
from pynorare import log
import attr
from collections import OrderedDict, defaultdict
from cldfcatalog import Config
from pyconcepticon import Concepticon
from clldutils.source import Source
import pybtex.database



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
    language = attr.ib()
    source = attr.ib()


@attr.s
class ConceptSetMeta(object):
    id = attr.ib()
    author = attr.ib()
    year = attr.ib()
    tags = attr.ib(repr=False, converter=lambda x: [y.strip() for y in
        x.split(',')] if isinstance(x, str) else x)
    source_language = attr.ib(repr=False)
    target_language = attr.ib(repr=False)
    url = attr.ib(repr=False)
    refs = attr.ib(repr=False)
    note = attr.ib(repr=False)
    alias = attr.ib(repr=False)
    norare = attr.ib(default=None, repr=False)
    path = attr.ib(default=None, repr=False)

    @property
    def concepts(self):
        tbg = TableGroup.from_file(self.path)
        concepts = OrderedDict()
        for row in tbg.tabledict[self.id+'.tsv']:
            concepts[row['CONCEPTICON_ID']] = OrderedDict({k.lower(): v for k,
                v in row.items()})
        return concepts
    
    @property
    def columns(self):
        tbg = TableGroup.from_file(self.path)
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
                    source=self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'source': ''})['source'] or self.refs,
                    language = self.norare.annotations[self.id].get(
                        c.name.lower(),
                        {'language': ''})['language'],
                    nameinsource=str(c.titles) if c.titles else ''
                    )

        return columns


@attr.s
class NoRaRe():
    """
    Basic class for handling the norms-rates-relations data.
    """
    repos = attr.ib(default=None, converter=Path)
    datasets = attr.ib(default=OrderedDict())

    def __attrs_post_init__(self):
        
        concepticon = Concepticon(Config.from_file().get_clone('concepticon'))
        datasets = set()
        self.annotations = defaultdict(lambda : OrderedDict())
        with UnicodeDictReader(self.repos.joinpath('norare.tsv'), delimiter='\t') as reader:
            for row in reader:
                self.annotations[row['DATASET']][row['NAME'].lower()] = {
                        k.lower(): row[k] for k in ['DATASET', 'NAME',
                        'LANGUAGE', 'STRUCTURE',
                            'TYPE', 'NORARE', 'RATING', 'SOURCE', 'NOTE']}
                datasets.add(row['DATASET'])

        with UnicodeDictReader(self.repos.joinpath('concept_set_meta.tsv'),
                delimiter='\t') as reader:
            for row in reader:
                row['norare'] = self
                row['path'] = self.repos.joinpath('concept_set_meta',
                        row['ID'], row['ID']+'.tsv-metadata.json').as_posix()
                self.datasets[row['ID']] = ConceptSetMeta(
                        **{k.lower(): v for k, v in row.items()})
                self.datasets[row['ID']].source_language = [
                    l.lower().strip(
                        ) for l in self.datasets[row['ID']].source_language.split(',')]

        # remaining datasets come from concepticon, we identify them from
        # datasets
        concepticon_datasets = [d for d in datasets if d not in self.datasets]
        for dataset in concepticon_datasets:
            ds = concepticon.conceptlists[dataset]
            self.datasets[ds.id] = ConceptSetMeta(
                    id=ds.id,
                    author=ds.author,
                    year=ds.year,
                    tags=', '.join(ds.tags),
                    source_language=ds.source_language,
                    target_language=ds.target_language,
                    url=ds.url,
                    refs=ds.refs,
                    note=ds.note,
                    alias=ds.alias,
                    norare=self,
                    path=concepticon.repos.joinpath(
                        'concepticondata', 'conceptlists', ds.id+'.tsv-metadata.json').as_posix()
                    )


        # get bibliography
        self.refs = OrderedDict()
        with self.repos.joinpath('references',
                'references.bib').open(encoding='utf-8') as fp:
            for key, entry in pybtex.database.parse_string(
                    fp.read(), bib_format='bibtex').entries.items():
                self.refs[key] = Source.from_entry(key, entry)



    def __iter__(self):
        return iter(self.norms)


