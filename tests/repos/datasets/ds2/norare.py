
def download(dataset):
    dataset.download_zip('http://example.com/f.xlsx.zip', 'f.zip', 'norare.xlsx')


def map(dataset, concepticon, mappings):
    dataset.extract_data('norare.xlsx', concepticon, mappings, gloss='FRENCH', language='fr')
