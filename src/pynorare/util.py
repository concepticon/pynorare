import csv
from itertools import islice, zip_longest

from tqdm import tqdm


class NoRaReError(Exception):
    # Challenge of the day:  Try saying NoRaReError three times in a row
    # without tripping over your tongue. :P
    pass


def read_wellformed_tsv_or_die(file_name):
    with open(file_name, encoding='utf-8') as f:
        rdr = csv.reader(f, delimiter='\t')
        table = list(rdr)

    if not table:
        raise NoRaReError(f'{file_name}: file empty')
    empty_rows = [
        row_no
        for row_no, row in enumerate(islice(table, 1, None), 2)
        if not row or all(not cell for cell in row)]
    if empty_rows:
        raise NoRaReError('\n'.join(
            f'{file_name}: {row_no}: empty row'
            for row_no in empty_rows))

    header = table[0]

    trailing_cells = [
        (row_no, len(row))
        for row_no, row in enumerate(islice(table, 1, None), 2)
        if any(islice(row, len(header), None))]
    if trailing_cells:
        raise NoRaReError('\n'.join(
            f'{file_name}: {row_no}: trailing cells'
            for row_no, row_width in trailing_cells))

    return [
        {h: c for h, c in zip_longest(header, row, fillvalue='') if h}
        for row in islice(table, 1, None)]


def progressbar(iterable=None, **kw):
    kw.setdefault('leave', False)
    kw.setdefault('desc', 'norare')
    return tqdm(iterable=iterable, **kw)
