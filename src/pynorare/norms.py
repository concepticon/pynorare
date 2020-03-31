from csvw import UnicodeDictReader
from cldfcatalog import Config
from collections import OrderedDict
from pyconcepticon import Concepticon

class Norms(Concepticon):

    def __init__(self, normdata=None, repos=None, delimiter="\t"):
        
        normdata = normdata or Config.from_file().get_clone('concepticon').joinpath('normdata.tsv')
        repos = repos or Config.from_file().get_clone('concepticon')
        Concepticon.__init__(self, repos)
        self.norms = OrderedDict()
        with UnicodeDictReader(normdata, delimiter=delimiter) as reader:
            for line in reader:
                self.norms[line['Conceptlist'], line['ColumnName']] = line

    def __iter__(self):
        return iter(self.norms)
