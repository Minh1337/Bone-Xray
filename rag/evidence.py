"""Experimental lexical question coverage, not entailment or medical authorization."""

import json
import re
import unicodedata
from pathlib import Path

try:
    from rag.lexical import STOPWORDS, fold
except ModuleNotFoundError:
    from lexical import STOPWORDS, fold


EVIDENCE_CONFIG = Path(__file__).resolve().parent / 'data' / 'evidence_config.json'


class EvidenceVerifier:
    def __init__(self, corpus_rows, config=None):
        self.config = config if config is not None else json.loads(EVIDENCE_CONFIG.read_text(encoding='utf-8'))
        self.concepts = {item['id']: item for item in self.config['concepts']}
        self.aliases = sorted([(fold(alias).split(), item['id']) for item in self.concepts.values()
                               for alias in item['aliases']], key=lambda pair: -len(pair[0]))
        self.neutral_phrases = sorted([fold(p).split() for p in self.config['neutral_phrases']], key=len, reverse=True)
        self.neutral_words = set(self.config['neutral_words'].split()) | STOPWORDS
        self.texts = {row['chunk_id']: fold(row['text']) for row in corpus_rows}
        self.contexts = {row['chunk_id']: fold(row.get('title', '') + ' ' + row.get('section', ''))
                         for row in corpus_rows}
        self.vocabulary = set(' '.join(self.texts.values()).split())

    def parse(self, question):
        # Preserve distinctions that accent folding alone would collapse: đau/đâu, mẫu/máu.
        question = unicodedata.normalize('NFC', question.casefold())
        for vietnamese, english in [('đâu', 'where'), ('mẫu', 'sample'), ('máu', 'blood')]:
            question = re.sub(r'\b' + vietnamese + r'\b', english, question)
        words = fold(question).split()
        concepts, literals, unknown = [], [], []
        position = 0
        while position < len(words):
            for alias, identifier in self.aliases:
                if words[position:position + len(alias)] == alias:
                    concepts.append(identifier)
                    position += len(alias)
                    break
            else:
                neutral = next((p for p in self.neutral_phrases if words[position:position + len(p)] == p), None)
                if neutral:
                    position += len(neutral)
                    continue
                word = words[position]
                if word not in self.neutral_words and not word.isdigit():
                    (literals if word in self.vocabulary else unknown).append(word)
                position += 1
        return {'concepts': list(dict.fromkeys(concepts)), 'literal_terms': list(dict.fromkeys(literals)),
                'unknown_terms': list(dict.fromkeys(unknown))}

    @staticmethod
    def has(text, phrase):
        return ' ' + fold(phrase) + ' ' in ' ' + text + ' '

    def check(self, question, candidates, *, top_k, rerank_only=False):
        parsed = self.parse(question)
        required = parsed['concepts'] + ['literal:' + word for word in parsed['literal_terms']]
        profiles = []
        specific = any(self.concepts[c].get('kind') == 'entity' for c in parsed['concepts'])
        for rank, hit in enumerate(candidates):
            identifier = hit['chunk_id']
            text, context = self.texts[identifier], self.contexts[identifier]
            matched = []
            for concept in parsed['concepts']:
                item = self.concepts[concept]
                # The document heading may establish a disease, but it cannot prove a requested fact.
                evidence = context + ' ' + text if item.get('kind') in {'entity', 'generic_entity'} else text
                if any(self.has(evidence, term) for term in item['evidence']):
                    matched.append(concept)
            matched.extend('literal:' + word for word in parsed['literal_terms'] if self.has(text, word))
            missing = [term for term in required if term not in matched]
            generic_title = not specific and any(
                self.concepts[c].get('kind') == 'generic_entity'
                and any(self.has(context, term) for term in self.concepts[c]['evidence'])
                for c in parsed['concepts'])
            profiles.append({'hit': hit, 'matched': matched, 'missing': missing,
                             'complete': bool(required) and not missing,
                             'generic_title': bool(generic_title), 'original_rank': rank})
        profiles.sort(key=lambda p: (-int(p['complete']), -int(p['generic_title']),
                                     -len(p['matched']), p['original_rank']))
        full = [p for p in profiles if p['complete']]
        diagnostics = {**parsed, 'checker_version': self.config['version'],
                       'check_type': 'lexical_coverage_not_entailment', 'candidate_count': len(candidates),
                       'rerank_only': rerank_only,
                       'complete_candidate_count': len(full),
                       'best_missing': profiles[0]['missing'] if profiles else required}
        if rerank_only:
            hits = [{**profile['hit'], 'evidence_coverage': {'matched': profile['matched'], 'missing': profile['missing']}}
                    for profile in profiles[:top_k]]
            return hits, 'concept_reranking_not_evidence_verification', diagnostics
        if self.config['require_known_query_terms'] and parsed['unknown_terms']:
            return [], 'unrecognized_question_terms', diagnostics
        if not full:
            return [], 'question_concepts_not_covered', diagnostics
        hits = [{**profile['hit'], 'evidence_coverage': {'matched': profile['matched'], 'missing': []}}
                for profile in full[:top_k]]
        return hits, 'lexically_covered_candidates_not_verified', diagnostics
