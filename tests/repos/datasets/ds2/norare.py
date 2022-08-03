
def download(dataset):
    dataset.download_zip('http://example.com/f.xlsx.zip', 'f.zip', 'norare.xlsx')


def map(dataset, concepticon, mappings):
    sheet = dataset.get_excel('norare.xlsx', 0, dicts=True)
    dataset.extract_data(sheet, concepticon, mappings, gloss='FRENCH', language='fr')
