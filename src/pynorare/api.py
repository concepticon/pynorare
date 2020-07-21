import collections

from csvw.metadata import TableGroup
from csvw.dsv import reader
import attr
from cldfcatalog import Config
from pyconcepticon import Concepticon
from clldutils.source import Source
from clldutils.apilib import API
import pybtex.database

__all__ = ['NoRaRe']


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
    other = attr.ib()


@attr.s
class ConceptSetMeta(object):
    id = attr.ib()
    author = attr.ib()
    year = attr.ib()
    tags = attr.ib(
        repr=False,
        converter=lambda x: [y.strip() for y in x.split(',')] if isinstance(x, str) else x)
    source_language = attr.ib(repr=False)
    target_language = attr.ib(repr=False)
    url = attr.ib(repr=False)
    refs = attr.ib(repr=False)
    note = attr.ib(repr=False)
    alias = attr.ib(repr=False)
    norare = attr.ib(default=None, repr=False)
    path = attr.ib(default=None, repr=False)

    @property
    def table(self):
        return TableGroup.from_file(self.path).tabledict[self.id + '.tsv']

    @property
    def concepts(self):
        concepts = collections.OrderedDict()
        for row in self.table:
            concepts[row['CONCEPTICON_ID']] = collections.OrderedDict(
                [(k.lower(), v) for k, v in row.items()])
        return concepts

    @property
    def columns(self):
        columns = collections.OrderedDict(
            [(c.name.lower(), {'nameinsource': str(c.titles) if c.titles else ''})
             for c in self.table.tableSchema.columns])

        for c in self.table.tableSchema.columns:
            columns[c.name.lower()] = Column(
                dataset=self.id,
                name=c.name.lower(),
                structure=self.norare.annotations[self.id].get(
                    c.name.lower(), {'structure': ''})['structure'],
                type=self.norare.annotations[self.id].get(
                    c.name.lower(), {'type': ''})['type'],
                norare=self.norare.annotations[self.id].get(
                    c.name.lower(), {'norare': ''})['norare'],
                rating=self.norare.annotations[self.id].get(
                    c.name.lower(), {'rating': ''})['rating'],
                note=self.norare.annotations[self.id].get(
                    c.name.lower(), {'note': ''})['note'],
                source=self.norare.annotations[self.id].get(
                    c.name.lower(), {'source': ''})['source'] or self.refs,
                language=self.norare.annotations[self.id].get(
                    c.name.lower(), {'language': ''})['language'],
                nameinsource=str(c.titles) if c.titles else '',
                other=self.norare.annotations[self.id].get(
                    c.name.lower(), {'other': ''})['other'])

        return columns


class NoRaRe(API):
    """
    Basic class for handling the norms-rates-relations data.
    """
    def __init__(self, repos=None, datasets=None, concepticon=None):
        API.__init__(self, repos)
        self.datasets = datasets or collections.OrderedDict()

        concepticon = concepticon
        if not concepticon:  # pragma: no cover
            try:
                concepticon = Concepticon(Config.from_file().get_clone('concepticon'))
            except KeyError:
                pass

        datasets = set()
        self.annotations = collections.defaultdict(lambda: collections.OrderedDict())
        for row in reader(self.repos / 'norare.tsv', delimiter='\t', dicts=True):
            self.annotations[row['DATASET']][row['NAME'].lower()] = {
                k.lower(): row[k] for k in [
                    'DATASET', 'NAME',
                    'LANGUAGE', 'STRUCTURE',
                    'TYPE', 'NORARE', 'RATING', 'SOURCE', 'OTHER', 'NOTE']}
            datasets.add(row['DATASET'])

        # get bibliography
        self.refs = collections.OrderedDict()
        with self.repos.joinpath('references', 'references.bib').open(encoding='utf-8') as fp:
            for key, entry in pybtex.database.parse_string(
                    fp.read(), bib_format='bibtex').entries.items():
                self.refs[key] = Source.from_entry(key, entry)

        all_refs = set(self.refs)
        if concepticon:
            all_refs = all_refs.union(concepticon.bibliography)

        for row in reader(self.repos / 'concept_set_meta.tsv', delimiter='\t', dicts=True):
            row['norare'] = self
            row['path'] = self.repos.joinpath(
                'concept_set_meta', row['ID'], row['ID'] + '.tsv-metadata.json')
            self.datasets[row['ID']] = ConceptSetMeta(**{k.lower(): v for k, v in row.items()})
            self.datasets[row['ID']].source_language = [
                l.lower().strip() for l in self.datasets[row['ID']].source_language.split(',')]

        # remaining datasets come from concepticon, we identify them from datasets
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
                    'concepticondata', 'conceptlists', ds.id + '.tsv-metadata.json')
            )

        for dataset in self.datasets.values():
            if dataset.refs:
                refs = [dataset.refs] if isinstance(dataset.refs, str) else dataset.refs
                for ref in refs:
                    if ref not in all_refs:  # pragma: no cover
                        raise ValueError('missing references.bib: {}'.format(ref))
