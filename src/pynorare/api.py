import types
import logging
import pathlib
import zipfile
import functools
import collections
import dataclasses
import urllib.error
import urllib.parse
import urllib.request
import importlib.util
import importlib.machinery
from typing import Literal, Optional, Union, Any

from csvw.metadata import TableGroup, Table, Column
from csvw.dsv import reader
from cldfcatalog import Config
from pyconcepticon import Concepticon
from clldutils.source import Source
from clldutils.apilib import API
import simplepybtex.database

from pynorare.files import get_mappings, get_excel, download_file, MappingsType
from pynorare.util import read_wellformed_tsv_or_die

__all__ = ['NoRaRe']


@dataclasses.dataclass
class Variable:
    dataset: 'Dataset'
    name: str
    structure: Literal[
        'cardinality', 'linguistic', 'logarithmic', 'magnitude', 'mean', 'normalized', 'numeric',
        'object', 'ordinality', 'percentage', 'semantic', 'standardized', 'sum', 'tokens']
    type: str
    norare: Literal['ratings', 'norms', 'relations']
    rating: str
    note: str
    language: str
    source: Optional[str]
    other: Optional[str]
    nameinsource: Union[str, bool] = False


@dataclasses.dataclass
class Dataset:
    id: str
    author: str
    year: int
    tags: list[str] = dataclasses.field(repr=False)
    source_language: list[str] = dataclasses.field(repr=False)
    target_language: str = dataclasses.field(repr=False)
    url: str = dataclasses.field(repr=False)
    refs: str = dataclasses.field(repr=False)
    note: str = dataclasses.field(repr=False)
    alias: str = dataclasses.field(repr=False)
    csvwmdpath: pathlib.Path = dataclasses.field(repr=False)
    variables: list[Variable] = dataclasses.field(repr=False)
    from_concepticon: bool
    norare_dsdir: pathlib.Path
    log: logging.Logger = dataclasses.field(default_factory=lambda: logging.getLogger(__name__))

    @staticmethod
    def _split(s):
        if isinstance(s, str):
            return [y.strip() for y in s.split(',')]
        assert isinstance(s, list)
        return s

    def __post_init__(self):
        self.tags = self._split(self.tags)
        self.source_language = self._split(self.source_language)
        self.csvwmdpath = pathlib.Path(self.csvwmdpath)
        if not self.csvwmdpath.exists():
            raise ValueError(self.csvwmdpath)
        self.norare_dsdir = pathlib.Path(self.norare_dsdir)

        colname2title = {
            c.name: str(c.titles) if c.titles else '' for c in self.table.tableSchema.columns}
        try:
            for v in self.variables:
                v.nameinsource = colname2title[v.name]
        except KeyError:
            pass

    @property
    def raw_dir(self) -> pathlib.Path:
        d = self.norare_dsdir / 'raw'
        if not self.from_concepticon and not d.exists():
            d.mkdir()
        return d

    @property
    def module(self) -> Optional[types.ModuleType]:
        modp = self.norare_dsdir / 'norare.py'
        if modp.exists():
            loader = importlib.machinery.SourceFileLoader(
                f"norare.{self.id.replace('-', '_')}", str(modp))
            mod = importlib.util.module_from_spec(
                importlib.util.spec_from_loader(loader.name, loader))
            loader.exec_module(mod)
            return mod
        else:
            return None

    @property
    def table(self) -> Table:
        return TableGroup.from_file(self.csvwmdpath).tabledict[self.id + '.tsv']

    @property
    def columns(self) -> list[Column]:
        return self.table.tableSchema.columns

    @property
    def concepts(self) -> collections.OrderedDict[str, collections.OrderedDict[str, Any]]:
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

    def _run_function(self, name: str, *args, **kw) -> None:
        if self.module and hasattr(self.module, name):
            self.log.info('%s: Running "%s"', self.id, name)
            getattr(self.module, name)(self, *args, **kw)
        else:  # pragma: no cover
            self.log.warning('%s: Function "%s" is not defined', self.id, name)

    def map(self, concepticon=None, mappings: Optional[MappingsType] = None):
        if not mappings:
            mappings, _ = get_mappings(concepticon)
        self._run_function('map', concepticon, mappings)

    def download(self):
        self._run_function('download')

    def download_zip(self, url, target=None, filename=None, cls=zipfile.ZipFile):
        with self.download_file(url, target=target).open('rb') as f:
            with cls(f) as archive:
                archive.extract(filename or archive.infolist()[0], path=str(self.raw_dir))
        self.log.info('Downloaded and unzipped %s successfully.', url)

    def download_file(self, url, target=None, overwrite=False):
        if not self.raw_dir.exists():
            self.raw_dir.mkdir()
        if not target:
            target = urllib.parse.urlparse(url).path.split('/')[-1]
        if (not self.raw_dir.joinpath(target).exists()) or overwrite:
            download_file(url, self.raw_dir / target)
            self.log.info('Downloaded %s successfully.', url)
        return self.raw_dir / target

    def get_csv(self, path, delimiter="\t", dicts=True, coding="utf-8"):
        self.log.info('load data from %s', path)
        return list(reader(self.raw_dir / path, delimiter=delimiter, dicts=dicts, encoding=coding))

    def get_excel(self, path, sidx=0, dicts=True):
        sheet = get_excel(self.raw_dir.joinpath(path), sidx, dicts)
        self.log.info('load data from %s', path)
        return sheet

    def extract_data(
            self,
            dicts: Union[str, list[dict[str, Any]]],
            concepticon: Concepticon,
            mappings: MappingsType,
            gloss: str = 'ENGLISH',
            language: str = 'en',
            pos: bool = False,
            pos_mapper: Optional[dict[str, str]] = None,
            pos_name: str = 'POS',
    ):
        """Extract data and write it to a file."""
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
        for _, rows in sorted(mapped.items(), key=lambda x: x[0]):
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
        for key, entry in simplepybtex.database.parse_string(
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
            csvwmdpath = datasetsdir / dataset / f'{dataset}.tsv-metadata.json'
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
                        raise ValueError(f'missing references.bib: {ref}')
