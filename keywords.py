import os
from collections import defaultdict
import spacy
import json


class KeywordsExtractor:
    def __init__(self, rake_stopwords_path='', language='en'):
        lang2spacy_model = {'en': 'en_core_web_lg'}
        self.nlp = spacy.load(lang2spacy_model[language], disable=['ner', 'textcat'])
        if os.path.exists(rake_stopwords_path):
            with open(rake_stopwords_path + '\\' + language + '.json', errors='ignore') as fp:
                self.stopwords = json.loads('\n'.join(fp.readlines()))['stop_words']
        else:
            self.stopwords = []

    def filter_chunk(self, chunk):
        chunk_filtered = []
        if chunk.text in self.stopwords:
            return ''
        for word in chunk:
            if word.pos_ == '-PRON-':
                continue
            if word.is_stop:
                continue
            if word.pos_ == 'DET':
                continue
            if word.lemma_ in self.stopwords:
                continue
            if word.lemma_.isalpha() and len(word.lemma_) == 1:
                continue
            if word.lemma_.isnumeric():
                continue
            if word.lemma_ == '-PRON-':
                continue
            chunk_filtered.append(word.lemma_)

        deduped = []
        prev = ''
        for word in chunk_filtered:
            word = word.lower().strip()
            if word == prev:
                continue
            prev = word
            deduped.append(word)
        return ' '.join(deduped)

    def post_filter(self, phrase):
        if len(phrase) < 3:
            return False
        # phrase = self.nlp(phrase)
        # if len(phrase) == 1 and phrase[0].pos_ == 'NOUN'\
        #   and len(phrase.ents) == 0: return False
        return True

    def get_keywords(self, sents):
        phrases = defaultdict(int)
        words_bonus = defaultdict(int)
        phrase2text = defaultdict(set)
        for sent in sents:
            sent = self.nlp(sent)

            for chunk in sent.noun_chunks:
                chunk_norm = self.filter_chunk(chunk)
                if not chunk_norm:
                    continue
                phrases[chunk_norm] += 1
                phrase2text[chunk_norm].add(chunk.text)
                for word in chunk_norm.split():
                    words_bonus[word] += 1

        keyphrases = {}

        for chunk, count in phrases.items():
            bonus = count
            for word in chunk.split():
                bonus += words_bonus[word]
            keyphrases[chunk] = bonus
        keyphrases = sorted(keyphrases.items(), key=lambda x: x[1], reverse=True)

        out_keyphrases = []
        for phrase, score in keyphrases:
            if self.post_filter(phrase) and score > 1:
                for text in phrase2text[phrase]:
                    out_keyphrases.append((phrase, score, text))

        return out_keyphrases


keywords_extractor = KeywordsExtractor(os.getcwd())
keywords = keywords_extractor.get_keywords(['Hi Edan, How was your vacation? Happy birthday by the way'])
print(keywords)
