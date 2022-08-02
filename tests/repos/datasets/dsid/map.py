from pynorare.dataset import NormDataSet

class Dataset(NormDataSet):
    def download(self):
        self.download_file('http://example.com', 'data.csv')

    def map(self):
        self.extract_data(
            self.get_csv('data.csv', dicts=True, delimiter=','), gloss='FRENCH', language='fr')
        self.extract_data(
            self.get_csv('data.csv', dicts=True, delimiter=','),
            pos=True,
            pos_mapper={'noun': 'THING'},
            gloss='FRENCH',
            language='fr')
