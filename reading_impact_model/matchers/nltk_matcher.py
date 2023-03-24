from typing import List

import nltk

from reading_impact_model.matchers import matcher
from reading_impact_model.impact_model import ImpactModel, ImpactMatch


class NLTKMatcher(matcher.ImpactMatcher):

    def __init__(self, parser, lang: str = 'en', impact_model: ImpactModel = None):
        super().__init__(lang=lang, impact_model=impact_model)
        self.parser = parser
        self.lang = lang
        self.impact_model = impact_model

    def find_impact_matches(self, sentence: str) -> List[ImpactMatch]:
        """Return reading impact matches for a given sentence."""

    def analyse_text(self, text: str):
        sents = nltk.tokenize.sent_tokenize(text, language=self.lang)
        for sent in sents:
            tokens = nltk.tokenize.word_tokenize(sent)