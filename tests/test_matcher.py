from unittest import TestCase
from reading_impact_model import matcher
from reading_impact_model import impact_model


class TestMatcher(TestCase):

    def setUp(self) -> None:
        self.matcher = matcher.ImpactMatcher(lang='nl')

    def test_is_wildcard_term_with_plain_term(self):
        self.assertEqual(False, matcher.is_wildcard_term('meeslepend'))

    def test_is_wildcard_term_with_exception_term(self):
        self.assertEqual(False, matcher.is_wildcard_term('*zucht*'))

    def test_is_wildcard_term_with_prefix_wildcard(self):
        self.assertEqual(True, matcher.is_wildcard_term('*boek'))

    def test_is_wildcard_term_with_postfix_wildcard(self):
        self.assertEqual(True, matcher.is_wildcard_term('verhaal*'))

    def test_is_wildcard_term_with_pre_and_postfix_wildcard(self):
        self.assertEqual(True, matcher.is_wildcard_term('*verhaal*'))

    def test_is_wildcard_term_with_infix_wildcard(self):
        self.assertEqual(True, matcher.is_wildcard_term('kinder*boek'))

    def test_wildcard_term_match_finds_prefix_match(self):
        sentence_term = 'kinderboek'
        match_term = '*boek'
        self.assertEqual(True, matcher.wildcard_term_match(sentence_term, match_term))

    def test_wildcard_term_match_finds_postfix_match(self):
        sentence_term = 'verhaallijn'
        match_term = 'verhaal*'
        self.assertEqual(True, matcher.wildcard_term_match(sentence_term, match_term))

    def test_wildcard_term_match_finds_infix_match(self):
        sentence_term = 'kinderliederenboek'
        match_term = 'kinder*boek'
        self.assertEqual(True, matcher.wildcard_term_match(sentence_term, match_term))


class TestMatcherComplexModel(TestCase):

    def setUp(self) -> None:
        impact_rule = {
            'Impact_term': 'goed (geschreven|omschreven|beschreven)',
            'Impact_group': 'verb_continuous_phrase',
            'Category': 'S',
            'Condition': '',
            'Neg-filter': '',
            'Comments': ''
        }
        model = {
            'impact_rules': [impact_rule]
        }
        model_test = impact_model.ImpactModel(model_json=model)
        self.matcher = matcher.ImpactMatcher(impact_model=model_test)

    def test_rule_term_indexer_handles_phrases(self):
        for term in self.matcher.impact_rule_term_index:
            print(term)
