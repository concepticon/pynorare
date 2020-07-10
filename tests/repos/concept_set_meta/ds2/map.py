from pynorare.dataset import NormDataSet


class Dataset(NormDataSet):
    id = "ds2"

    def download(self):
        self.download_zip('http://example.com/f.xlsx.zip', 'f.zip', 'norare.xlsx')

    def map(self):
        sheet = self.get_excel('norare.xlsx', 0, dicts=True)
        self.extract_data(sheet, gloss='FRENCH', language='fr')
