from unittest import TestCase
from reading_impact_model.matchers import matcher
from reading_impact_model import impact_model
from reading_impact_model.impact_model import CONDITION_MATCH_FIELDS


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


class TestMatcherSentenceSetting(TestCase):

    def setUp(self) -> None:
        self.matcher = matcher.ImpactMatcher(lang='en')

    def test_set_sentence(self):
        sentence = 'This is a beautifully written, stylistically interesting sentence'
        self.matcher._set_sentence(sentence)
        print(self.matcher.sentence_vocab_terms)
        self.assertEqual(True, 'beautifully' in self.matcher.sentence_vocab_terms)

    def test_set_sentence_indexes_wildcard_terms(self):
        sentence = 'This is a beautifully written, stylistically interesting sentence'
        self.matcher._set_sentence(sentence)
        print(self.matcher.sentence_vocab_terms)
        self.assertEqual(True, 'written' in self.matcher.sentence_vocab_terms)
        self.assertEqual(True, 'stylistic*' in self.matcher.sentence_vocab_terms)


class TestMatcherAnalyseText(TestCase):

    def setUp(self) -> None:
        self.matcher = matcher.ImpactMatcher(lang='en')

    def test_matcher_returns_matches(self):
        sentence = 'The writing is beautiful'
        matches = self.matcher.find_impact_matches(sentence)
        self.assertEqual(2, len(matches))

    def test_matcher_analyse_text_sets_sentence_index(self):
        sentence = 'The writing is beautiful'
        matches = self.matcher.analyse_text(sentence)
        for match in matches:
            self.assertEqual(True, match['sentence_index'] is not None)

    def test_matcher_analyse_text_matches_include_condition_fields(self):
        sentence = 'The writing is beautiful'
        matches = self.matcher.analyse_text(sentence)
        for match in matches:
            for field in CONDITION_MATCH_FIELDS:
                self.assertEqual(True, field in match)
