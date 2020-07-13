"""
Create data for the web-application.
"""
import json
import collections


def run(args):
    meta, data = {}, collections.defaultdict(dict)
    for i, ds in enumerate(args.api.datasets.values()):
        args.log.info('analyze ' + ds.id)
        meta[ds.id] = {
            'author': ds.author,
            'year': ds.year,
            'tags': ds.tags,
            'source_languages': ds.source_language,
            'target_languages': ds.target_language,
        }
        for cid, concept_ in ds.concepts.items():
            concept = {}
            for colid, column in ds.columns.items():
                if colid in args.api.annotations[ds.id]:
                    concept[colid] = {
                        'value': concept_[colid],
                        'language': column.language,
                        'norare': column.norare,
                        'type': column.type,
                        'other': column.other,
                        'structure': column.structure,
                    }
            if concept_['concepticon_gloss']:
                data[str(cid) + '/' + concept_['concepticon_gloss']][ds.id] = concept

    args.norarepo.joinpath('app', 'data').mkdir(parents=True, exist_ok=True)
    with args.norarepo.joinpath('app', 'data', 'norare.js').open('w', encoding='utf8') as f:
        f.write('var NRRDATA = ' + json.dumps(data) + ';\n')
        f.write('var NRRMETA = ' + json.dumps(meta) + ';\n')
