def download(dataset):
    dataset.download_file('http://example.com/data.csv')


def map(dataset, concepticon, mappings):
    dataset.extract_data(
        dataset.get_csv('data.csv', dicts=True, delimiter=','),
        concepticon,
        mappings,
        gloss='FRENCH', language='fr')
    dataset.extract_data(
        dataset.get_csv('data.csv', dicts=True, delimiter=','),
        concepticon,
        mappings,
        pos=True,
        pos_mapper={'noun': 'THING'},
        gloss='FRENCH',
        language='fr')
