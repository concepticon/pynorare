"""
Create data for the web-application.
"""
from pathlib import Path
from tabulate import tabulate
from pynorare import NoRaRe
from tqdm import tqdm
from collections import defaultdict
import json

def run(args):

    norare = NoRaRe(args.norarepo)
    concepts = set()
    meta, data = {}, defaultdict(dict)
    for i, ds in enumerate(norare.datasets.values()):
        args.log.info('analyze '+ds.id)
        meta[ds.id] = {
                'author': ds.author,
                'year': ds.year,
                'tags': ds.tags,
                'source_languages': ds.source_language,
                'target_languages': ds.target_language
                }
        for cid, concept_ in ds.concepts.items():

            concept = {}
            visited = set()
            for colid, column in ds.columns.items():
                if colid in norare.annotations[ds.id]:
                    concept[colid] = {
                            'value': concept_[colid],
                            'language': column.language,
                            'norare': column.norare,
                            'type': column.type,
                            'other': column.other,
                            'structure': column.structure
                            }
            if concept_['concepticon_gloss']:
                data[str(cid)+'/'+concept_['concepticon_gloss']][ds.id] = concept

    with open(args.norarepo.joinpath('app', 'data', 'norare.js').as_posix(), 'w') as f:
        f.write('var NRRDATA = '+json.dumps(data)+';\n')
        f.write('var NRRMETA = '+json.dumps(meta)+';\n')
