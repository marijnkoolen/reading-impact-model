from unittest import TestCase
from reading_impact_model import impact_model


valid_model_json = {
  "impact_terms": [
    "bla"
  ],
  "aspect_terms": [
    "bla"
  ],
  "impact_rules": [
    "bla"
  ]
}

invalid_model_json = {
    "aspect_terms": [
        "bla"
    ]
}

class TestReadModel(TestCase):

    def test_read_model_json_file(self):
        model_json = impact_model.read_impact_model(model_file='tests/test_data/data_test_model.json')
        self.assertEqual(isinstance(model_json, dict), True)

    def test_read_invalid_model_json_file(self):
        error = None
        try:
            impact_model.read_impact_model(model_file='tests/test_data/data_test_model_invalid.json')
        except TypeError as err:
            error = err
        self.assertEqual(error is None, False)


class TestImpactModel(TestCase):

    def test_read_model_from_json_file(self):
        error = None
        try:
            impact_model.ImpactModel(model_file='reading_impact_model/models/impact_model-nl.json')
        except BaseException as err:
            error = err
        self.assertEqual(error, None)

    def test_read_nl_model(self):
        model = impact_model.load_model(lang='nl')
        self.assertEqual(isinstance(model, impact_model.ImpactModel), True)

    def test_read_en_model(self):
        model = impact_model.load_model(lang='en')
        self.assertEqual(isinstance(model, impact_model.ImpactModel), True)

    def test_read_default_model(self):
        model = impact_model.load_model()
        self.assertEqual(isinstance(model, impact_model.ImpactModel), True)

    def test_check_model_has_term(self):
        model = impact_model.load_model(lang='nl')
        term = 'meeslepend'
        self.assertEqual(model.has_impact_term(term), True)

class TestModelImpactVocabulary(TestCase):

    def setUp(self) -> None:
        impact_rules = [
            {
                'Impact_term': 'karakter',
                'Impact_group': 'noun_term',
                'Category': 'N',
                'Condition': '',
                'Neg-filter': '',
                'Comments': ''
            },
            {
                'Impact_term': '*boek',
                'Impact_group': 'noun_term',
                'Category': 'A',
                'Condition': '',
                'Neg-filter': '',
                'Comments': ''
            },
            {
                'Impact_term': 'verhaal*',
                'Impact_group': 'noun_term',
                'Category': 'S',
                'Condition': '',
                'Neg-filter': '',
                'Comments': ''
            }
        ]
        model = {
            'impact_rules': impact_rules
        }
        self.model = impact_model.ImpactModel(model_json=model)

    def test_vocab_has_plain_term(self):
        term = 'karakter'
        self.assertEqual(True, self.model.has_impact_term(term))

    def test_vocab_has_wildcard_term(self):
        term = '*boek'
        self.assertEqual(True, self.model.has_impact_term(term))

    def test_vocab_has_prefix_wildcard_term(self):
        term = 'kinderboek'
        self.assertEqual(True, self.model.has_impact_term(term))

    def test_vocab_has_postfix_wildcard_term(self):
        term = 'verhaallijn'
        self.assertEqual(True, self.model.has_impact_term(term))


class TestModelWildcardTerms(TestCase):

    def setUp(self):
        impact_rules = [
            {
                'Impact_term': '*verhaal',
                'Impact_group': 'noun_term',
                'Category': 'N',
                'Condition': '',
                'Neg-filter': '',
                'Comments': ''
            },
            {
                'Impact_term': '*boek',
                'Impact_group': 'noun_term',
                'Category': 'A',
                'Condition': '',
                'Neg-filter': '',
                'Comments': ''
            },
            {
                'Impact_term': 'verhaal*',
                'Impact_group': 'noun_term',
                'Category': 'S',
                'Condition': '',
                'Neg-filter': '',
                'Comments': ''
            }
        ]
        model = {
            'impact_rules': impact_rules
        }
        self.model = impact_model.ImpactModel(model_json=model)

    def test_model_has_prefix_wildcard_lengths(self):
        self.assertEqual(4 in self.model.prefix_wildcard_lengths, False)
        self.assertEqual(7 in self.model.prefix_wildcard_lengths, True)

    def test_model_has_postfix_wildcard_lengths(self):
        self.assertEqual(4 in self.model.postfix_wildcard_lengths, True)
        self.assertEqual(7 in self.model.postfix_wildcard_lengths, True)


class TestModelAspectVocabulary(TestCase):

    def setUp(self) -> None:
        self.model = impact_model.load_model(lang='nl')

    def test_vocab_has_plain_term(self):
        term = 'karakter'
        self.assertEqual(True, self.model.has_aspect_term(term))

    def test_vocab_has_wildcard_term(self):
        term = '*boek'
        self.assertEqual(True, self.model.has_aspect_term(term))

    def test_vocab_has_prefix_wildcard_term(self):
        term = 'kinderboek'
        self.assertEqual(True, self.model.has_aspect_term(term))

    def test_vocab_has_zero_prefix_wildcard_term(self):
        term = 'boek'
        self.assertEqual(True, self.model.has_aspect_term(term))

    def test_vocab_has_postfix_wildcard_term(self):
        term = 'verhaallijn'
        self.assertEqual(True, self.model.has_aspect_term(term))

    def test_get_term_group_returns_general(self):
        term = 'kinderboek'
        groups = self.model.get_term_groups(term)
        print('Groups:', groups)
        self.assertEqual(True, 'general' in groups)
