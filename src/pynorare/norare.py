from pathlib import Path
from csvw.metadata import TableGroup
from tqdm import tqdm
from pynorare import log


class NoRaRe():

    def __init__(self, repos=None):

        self.repos = Path(repos)
        self.datasets = {}

    def load_datasets(self):
        for dataset in tqdm(sorted(
                self.repos.joinpath('concept_set_meta').glob('*')),
                desc='loading datasets'):
            idx = dataset.name
            if dataset.joinpath(idx+'.tsv').exists() and dataset.joinpath(
                    idx+'.tsv-metadata.json').exists():
                self.get_dataset(dataset)

        log.info('loaded datasets')

    def get_dataset(self, dataset):
        if dataset in self.datasets:
            return self.datasets[dataset]
        else:
            tbg = TableGroup.from_file(
                    self.repos.joinpath(
                        'concept_set_meta',
                        dataset,
                        dataset+'.tsv-metadata.json').as_posix())
            self.datasets[dataset] = (
                    list(tbg.tabledict[dataset+'.tsv']),
                    [c.name for c in
                        tbg.tabledict[dataset+'.tsv'].tableSchema.columns]
                    )
            return self.datasets[dataset]

    def get_columns(self, dataset, *columns, dicts=True):
        out = []

        for row in self.get_dataset(dataset)[0]:
            out += [[row[h] for h in columns]]
        if dicts:
            return [{col: content for col, content in zip(
                columns,
                row)} for row in out]
        return out


    def __iter__(self):
        return iter(self.norms)
