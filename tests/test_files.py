from pynorare.files import get_mappings


def test_get_mappings(concepticon_api):
    mappings, _ = get_mappings(concepticon_api)
    # Make sure the sorting of mappings is correct:
    assert mappings['fr']['the gloss'][0] == ('2', 3, 'Person/Thing')
