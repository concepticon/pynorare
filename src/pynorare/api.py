import pathlib
import collections
import importlib.util
import importlib.machinery

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
class Variable(object):
    dataset = attr.ib()
    name = attr.ib()
    structure = attr.ib()
    type = attr.ib()
    norare = attr.ib(validator=attr.validators.in_(['ratings', 'norms', 'relations']))
    rating = attr.ib()
    note = attr.ib()
    language = attr.ib()
    source = attr.ib()
    other = attr.ib()
    nameinsource = attr.ib(default=False)


def existing_file(instance, attribute, value):
    if not (value.exists() and value.is_file()):
        raise ValueError(value)


@attr.s
class DatasetMeta(object):
    id = attr.ib()
    author = attr.ib()
    year = attr.ib()
    tags = attr.ib(
        repr=False,
        converter=lambda x: [y.strip() for y in x.split(',')] if isinstance(x, str) else x)
    source_language = attr.ib(
        repr=False,
        converter=lambda x: [y.strip() for y in x.split(',')] if isinstance(x, str) else x)
    target_language = attr.ib(repr=False)
    url = attr.ib(repr=False)
    refs = attr.ib(repr=False)
    note = attr.ib(repr=False)
    alias = attr.ib(repr=False)
    csvwmdpath = attr.ib(
        repr=False,
        converter=lambda s: pathlib.Path(s),
        validator=existing_file)
    variables = attr.ib(repr=False, validator=attr.validators.instance_of(list))
    from_concepticon = attr.ib(validator=attr.validators.instance_of(bool))
    norare_dsdir = attr.ib(converter=lambda s: pathlib.Path(s))

    def __attrs_post_init__(self):
        colname2title = {
            c.name: str(c.titles) if c.titles else '' for c in self.table.tableSchema.columns}
        for v in self.variables:
            v.nameinsource = colname2title[v.name]

    @property
    def module(self):
        modp = self.norare_dsdir / 'map.py'
        if modp.exists():
            loader = importlib.machinery.SourceFileLoader(
                'norare.{}'.format(self.id.replace('-', '_')), str(modp))
            mod = importlib.util.module_from_spec(
                importlib.util.spec_from_loader(loader.name, loader))
            loader.exec_module(mod)
            return mod

    @property
    def table(self):
        return TableGroup.from_file(self.csvwmdpath).tabledict[self.id + '.tsv']

    @property
    def concepts(self):
        concepts = collections.OrderedDict()
        for row in self.table:
            concepts[row['CONCEPTICON_ID']] = collections.OrderedDict(
                [(k.lower(), v) for k, v in row.items()])
        return concepts


class NoRaRe(API):
    """
    Basic class for handling the norms-rates-relations data.
    """
    def __init__(self, repos=None, concepticon=None):
        API.__init__(self, repos)
        self.datasets = collections.OrderedDict()
        datasetsdir = self.repos / 'datasets'

        concepticon = concepticon
        if not concepticon:  # pragma: no cover
            try:
                concepticon = Concepticon(Config.from_file().get_clone('concepticon'))
            except KeyError:
                pass

        variables = collections.defaultdict(list)
        for row in reader(self.repos / 'norare.tsv', delimiter='\t', dicts=True):
            variables[row['DATASET']].append(
                Variable(**{k.lower(): v for k, v in row.items()}))

        # get bibliography
        self.refs = collections.OrderedDict()
        for key, entry in pybtex.database.parse_string(
                self.repos.joinpath('references', 'references.bib').read_text(encoding='utf8'),
                bib_format='bibtex').entries.items():
            self.refs[key] = Source.from_entry(key, entry)

        all_refs = set(self.refs).union(concepticon.bibliography if concepticon else {})

        for row in reader(self.repos / 'datasets.tsv', delimiter='\t', dicts=True):
            self.datasets[row['ID']] = DatasetMeta(
                variables=variables[row['ID']],
                csvwmdpath=datasetsdir / row['ID'] / '{}.tsv-metadata.json'.format(row['ID']),
                from_concepticon=False,
                norare_dsdir=datasetsdir / row['ID'],
                **{k.lower(): v for k, v in row.items()})

        # remaining datasets come from concepticon, we identify them from datasets
        for dataset in [d for d in variables if d not in self.datasets]:
            csvwmdpath = datasetsdir / dataset / '{}.tsv-metadata.json'.format(dataset)
            ds = concepticon.conceptlists[dataset]
            self.datasets[ds.id] = DatasetMeta(
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
                variables=variables[dataset],
                csvwmdpath=csvwmdpath if csvwmdpath.exists() else concepticon.repos.joinpath(
                    'concepticondata', 'conceptlists', ds.id + '.tsv-metadata.json'),
                from_concepticon=True,
                norare_dsdir=datasetsdir / dataset,
            )

        for dataset in self.datasets.values():
            if dataset.refs:
                refs = [dataset.refs] if isinstance(dataset.refs, str) else dataset.refs
                for ref in refs:
                    if ref not in all_refs:  # pragma: no cover
                        raise ValueError('missing references.bib: {}'.format(ref))
