"""Small in-memory BM25 and reciprocal-rank fusion; no extra runtime service."""

import math
import re
import unicodedata
from collections import Counter

import numpy as np


STOPWORDS = set(('a an and are as at be been by can could did do does for from has have how i if in is it its '
                 'may of on or that the their then there these they this those to was were what when where which who '
                 'why will with would you your '
                 'ai ban bao benh bi cac can cau cho co cua da de den di do duoc gi giup hay hien hoi khi khong '
                 'la lam lieu mot nao nay nhu nhung o phai sao se the thi toi trong tu va vay ve voi').split())


def fold(text):
    text = unicodedata.normalize('NFKD', text.casefold().replace('đ', 'd'))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', text))


def contains(text, phrase):
    return f' {fold(phrase)} ' in f' {fold(text)} '


def tokens(text):
    return [word for word in fold(text).split() if word not in STOPWORDS and len(word) > 1]


def expansion(question, config):
    words = fold(question).split()
    vocabulary = sorted(((phrase.split(), value) for phrase, value in config['expansions'].items()),
                        key=lambda item: -len(item[0]))
    output = []
    position = 0
    matched = False
    while position < len(words):
        for phrase, translated in vocabulary:
            if words[position:position + len(phrase)] == phrase:
                output.extend(translated.split())
                position += len(phrase)
                matched = True
                break
        else:
            if words[position] not in STOPWORDS:
                output.append(words[position])
            position += 1
    return ' '.join(output) if matched else ''


class BM25:
    def __init__(self, corpus_rows, config):
        self.k1, self.b = config['bm25_k1'], config['bm25_b']
        documents = [tokens(row.get('title', '') + ' ' + row.get('section', '') + ' ' + row['text'])
                     for row in corpus_rows]
        self.lengths = np.array([len(doc) for doc in documents], dtype=np.float32)
        self.average = max(float(self.lengths.mean()), 1)
        self.postings = {}
        for index, doc in enumerate(documents):
            for term, count in Counter(doc).items():
                self.postings.setdefault(term, []).append((index, count))
        self.count = len(documents)

    def score(self, question):
        scores = np.zeros(self.count, dtype=np.float32)
        for term in set(tokens(question)):
            postings = self.postings.get(term, [])
            if not postings:
                continue
            idf = math.log(1 + (self.count - len(postings) + 0.5) / (len(postings) + 0.5))
            for i, frequency in postings:
                denominator = frequency + self.k1 * (1 - self.b + self.b * self.lengths[i] / self.average)
                scores[i] += idf * frequency * (self.k1 + 1) / denominator
        return scores


def fuse(rankings, count, constant, weights=None):
    scores = np.zeros(count, dtype=np.float64)
    for ranking, weight in zip(rankings, weights if weights is not None else [1] * len(rankings)):
        for rank, index in enumerate(ranking, 1):
            scores[index] += weight / (constant + rank)
    return scores
