from typing import Dict

from trankit import Pipeline

from reading_impact_model.matchers import matcher
from reading_impact_model.impact_model import ImpactModel


class TrankitMatcher(matcher.ImpactMatcher):

    def __init__(self, parser: Pipeline, lang: str = 'en', impact_model: ImpactModel = None,
                 **kwargs):
        super().__init__(lang=lang, impact_model=impact_model, **kwargs)
        self.parser = parser
        self.lang = lang

    def _iter_text_sentences(self, text: str):
        doc = self.parser(text)
        for si, sent in enumerate(doc['sentences']):
            self._set_sentence(sent)
            yield si

    def _set_sentence(self, sentence: Dict[str, any]) -> None:
        self._reset_sentence()
        self.sentence_string = sentence['text']
        for trankit_token in sentence['tokens']:
            token = {
                'word': trankit_token['text'],
                'lemma': trankit_token['lemma'],
                'pos': trankit_token['upos'].lower()
            }
            self.sentence_tokens.append(token)
            if token['pos'] != 'punct':
                self.add_candidate_rules(token['text'], token['lemma'])
