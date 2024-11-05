import logging
import pathlib
import zipfile
import functools
import collections
import urllib.error
import urllib.parse
import urllib.request
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

from pynorare.files import get_mappings, get_excel, download_file
from pynorare.util import read_wellformed_tsv_or_die

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
        raise ValueError(value)  # pragma: no cover


@attr.s
class Dataset(object):
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
    log = attr.ib(default=logging.getLogger(__name__))

    def __attrs_post_init__(self):
        colname2title = {
            c.name: str(c.titles) if c.titles else '' for c in self.table.tableSchema.columns}
        try:
            for v in self.variables:
                v.nameinsource = colname2title[v.name]
        except KeyError:
            pass

    @property
    def raw_dir(self):
        d = self.norare_dsdir / 'raw'
        if not self.from_concepticon and not d.exists():
            d.mkdir()
        return d

    @property
    def module(self):
        modp = self.norare_dsdir / 'norare.py'
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
    def columns(self):
        return self.table.tableSchema.columns

    @property
    def concepts(self):
        concepts = collections.OrderedDict()
        for row in self.table:
            concepts[row['CONCEPTICON_ID']] = collections.OrderedDict(
                [(k.lower(), v) for k, v in row.items()])
        return concepts

    def validate(self):
        mappings = list(self.table)
        if mappings:
            self.log.info('metadata file can be loaded')
        if 'CONCEPTICON_ID' in mappings[0] and \
                'CONCEPTICON_GLOSS' in mappings[0] and \
                'LINE_IN_SOURCE' in mappings[0]:
            self.log.info('concepticon data present in data')

    def _run_function(self, name, *args, **kw):
        if self.module and hasattr(self.module, name):
            self.log.info('{}: Running "{}"'.format(self.id, name))
            getattr(self.module, name)(self, *args, **kw)
        else:  # pragma: no cover
            self.log.warning('{}: Function "{}" is not defined'.format(self.id, name))

    def map(self, concepticon=None, mappings=None):
        if not mappings:
            mappings, _ = get_mappings(concepticon)
        self._run_function('map', concepticon, mappings)

    def download(self):
        self._run_function('download')

    def download_zip(self, url, target=None, filename=None, cls=zipfile.ZipFile):
        with self.download_file(url, target=target).open('rb') as f:
            with cls(f) as archive:
                archive.extract(filename or archive.infolist()[0], path=str(self.raw_dir))
        self.log.info('Downloaded and unzipped {0} successfully.'.format(url))

    def download_file(self, url, target=None, overwrite=False):
        if not self.raw_dir.exists():
            self.raw_dir.mkdir()
        if not target:
            target = urllib.parse.urlparse(url).path.split('/')[-1]
        if (not self.raw_dir.joinpath(target).exists()) or overwrite:
            try:
                urllib.request.urlretrieve(url, str(self.raw_dir / target))
            except urllib.error.HTTPError:  # pragma: no cover
                # Try with requests:
                download_file(url, self.raw_dir / target)
            self.log.info('Downloaded {0} successfully.'.format(url))
        return self.raw_dir / target

    def get_csv(self, path, delimiter="\t", dicts=True, coding="utf-8"):
        self.log.info('load data from {0}'.format(path))
        return list(reader(self.raw_dir / path, delimiter=delimiter, dicts=dicts, encoding=coding))

    def get_excel(self, path, sidx=0, dicts=True):
        sheet = get_excel(self.raw_dir.joinpath(path), sidx, dicts)
        self.log.info('load data from {0}'.format(path))
        return sheet

    def extract_data(self,
                     dicts,
                     concepticon,
                     mappings,
                     gloss='ENGLISH',
                     language='en',
                     pos=False,
                     pos_mapper=False,
                     pos_name='POS'):
        pos_mapper = pos_mapper or {}
        if isinstance(dicts, str):
            p = self.raw_dir.joinpath(dicts)
            if p.exists():
                conv = {
                    '.xlsx': self.get_excel,
                    '.xls': self.get_excel,
                    '.csv': functools.partial(self.get_csv, delimiter=','),
                    '.tsv': self.get_csv,
                }
                if p.suffix in conv:
                    dicts = conv[p.suffix](dicts)

        rename = {str(c.titles): c.name for c in self.columns if c.titles}
        # (conceptset ID, list of rows with matching glosses)
        mapped = collections.defaultdict(list)
        for i, row in enumerate(dicts, start=1):
            new_row = {rename.get(k, k): v for k, v in row.items()}
            new_row.setdefault('LINE_IN_SOURCE', i)
            gmappings = mappings[language].get(new_row[gloss])
            if gmappings:
                match, priority = None, None
                if pos:
                    for match, priority, pos_ in reversed(gmappings):
                        if pos_ == pos_mapper.get(new_row[pos_name], new_row[pos_name]) and match:
                            break  # pragma: no cover
                else:
                    match, priority, pos_ = gmappings[0]

                if match:
                    new_row['CONCEPTICON_ID'] = str(match)
                    new_row['CONCEPTICON_GLOSS'] = concepticon.conceptsets[match].gloss
                    new_row['_PRIORITY'] = priority
                    mapped[match].append(new_row)

        table = []
        for key, rows in sorted(mapped.items(), key=lambda x: x[0]):
            # We choose one representative gloss in the raw data for each conceptset ID, selecting
            # by higher priority and lower line number in the raw data.
            table.append(sorted(rows, key=lambda x: (-x['_PRIORITY'], x['LINE_IN_SOURCE']))[0])
        self.write_table(table)

    def write_table(self, items):
        self.table.write(items, base=self.norare_dsdir)


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
        for row in read_wellformed_tsv_or_die(self.repos / 'norare.tsv'):
            variables[row['DATASET']].append(
                Variable(**{k.lower(): v for k, v in row.items()}))

        # get bibliography
        self.refs = collections.OrderedDict()
        for key, entry in pybtex.database.parse_string(
                self.repos.joinpath('references', 'references.bib').read_text(encoding='utf8'),
                bib_format='bibtex').entries.items():
            self.refs[key] = Source.from_entry(key, entry)

        all_refs = set(self.refs).union(concepticon.bibliography if concepticon else {})

        for row in read_wellformed_tsv_or_die(self.repos / 'datasets.tsv'):
            self.datasets[row['ID']] = Dataset(
                variables=variables[row['ID']],
                csvwmdpath=datasetsdir / row['ID'] / '{}.tsv-metadata.json'.format(row['ID']),
                from_concepticon=False,
                norare_dsdir=datasetsdir / row['ID'],
                **{k.lower(): v for k, v in row.items()})

        # remaining datasets come from concepticon, we identify them from datasets
        for dataset in [d for d in variables if d not in self.datasets]:
            csvwmdpath = datasetsdir / dataset / '{}.tsv-metadata.json'.format(dataset)
            ds = concepticon.conceptlists[dataset]
            self.datasets[ds.id] = Dataset(
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
