from unittest import TestCase

import spacy

from reading_impact_model.matchers.spacy_matcher import SpacyMatcher
from reading_impact_model import impact_model


class TestMatcher(TestCase):

    def setUp(self) -> None:
        nlp = spacy.load('en_core_web_sm')
        self.matcher = SpacyMatcher(parser=nlp, lang='en')

    def test_matcher_has_model(self):
        self.assertEqual(True, isinstance(self.matcher.impact_model, impact_model.ImpactModel))

    def test_matcher_returns_matches(self):
        sentence = 'The writing is beautiful'
        matches = self.matcher.find_impact_matches(sentence)
        self.assertEqual(2, len(matches))

    def test_matcher_returns_scores(self):
        sentence = 'The writing is beautiful.'
        matches = self.matcher.find_impact_matches(sentence)
        print(matches)
        impact_matches = self.matcher.analyse_text(sentence)
        for match in impact_matches:
            print(match)
            self.assertEqual(True, 'positive' in match)
            self.assertEqual(1, match['positive'])
