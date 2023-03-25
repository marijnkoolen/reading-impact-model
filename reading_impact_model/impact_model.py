from __future__ import annotations
import json
import os
import pickle
from collections import defaultdict
from functools import partial
from typing import Dict, List, Set, Union


WILDCARD_EXCEPTIONS = {'*sigh*', '*zucht*'}
MIN_SUFFIX_LENGTH = 3

IMPACT_TYPES = {
    'en': {'positive', 'style', 'narrative', 'reflection', 'negative', 'surprise', 'attention', 'humor'},
    'nl': {'affect', 'style', 'narrative', 'reflection'}
}

IMPACT_MATCH_FIELDS = {'match_word', 'match_lemma', 'match_index', 'impact_term', 'impact_type', 'impact_term_type'}
CONDITION_MATCH_FIELDS = {'match_word', 'match_lemma', 'match_index', 'condition_term', 'condition_type'}


def is_wildcard_term(term):
    """
    Determine if term is a wildcard term, e.g. starts or ends with an asterix ("*").
    Wildcards on both sides are not allowed, since this is reserved for special terms.
    E.g. the asterixes in "*sigh*" (or *zucht* in Dutch) carry meaning on how to interpret "sigh".
    """
    wildcard_type = has_wildcard_type(term)
    return False if wildcard_type is None else True


def has_wildcard_type(term) -> Union[None, str]:
    if term in WILDCARD_EXCEPTIONS:
        return None
    if '*' not in term:
        return None
    if term[0] == '*':
        if term[-1] == '*':
            return 'both'
        else:
            return 'post'
    elif term[-1] == '*':
        return 'pre'
    elif '*' in term:
        return 'within'
    else:
        return None


def wildcard_term_match(sentence_term: str, match_term: str):
    """this function interprets wildcards in match terms and uses regex to match term against a sentence term"""
    if match_term[0] == "*" and match_term[-1] != '*':
        return sentence_term.endswith(match_term[1:])
    elif match_term[0] == '*' and match_term[-1] == '*':
        return match_term[1:-1] in sentence_term
    elif match_term[-1] == "*":
        return sentence_term.startswith(match_term[:-1])
    elif '*' in match_term:
        parts = match_term.split('*')
        if len(parts) > 2:
            raise ValueError('terms cannot have multiple infix wildcards')
        start, end = parts
        return sentence_term.startswith(start) and sentence_term.endswith(end)
    else:
        return False


class Token:

    def __init__(self, word: str, index: int, lemma: str = None, pos: str = None):
        self.word = word
        self.index = index
        self.lemma = lemma if lemma else word
        self.pos = pos


class Term:

    def __init__(self, term: str, group: str):
        self.string = term
        self.group = group
        self.has_wildcard: bool = False
        self.has_prefix_wildcard: bool = False
        self.has_postfix_wildcard: bool = False
        self.has_infix_wildcard: bool = False
        if '*' in self.string and self.string not in WILDCARD_EXCEPTIONS:
            self.has_wildcard = True
            self.has_prefix_wildcard: bool = True if self.string[0] == '*' else False
            self.has_postfix_wildcard: bool = True if self.string[-1] == '*' else False
            self.has_infix_wildcard: bool = True if '*' in self.string[1:-1] else False


class ImpactTerm(Term):

    def __init__(self, impact_string: str, impact_group: str, string_pos: str, group_type: str):
        assert(len(impact_string) > 0)
        super().__init__(impact_string, impact_group)
        self.pos = string_pos
        self.type = group_type

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


class AspectTerm(Term):

    def __init__(self, aspect_term: str, aspect_group: str):
        assert(len(aspect_term) > 0)
        super().__init__(aspect_term, aspect_group)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


class ImpactMatch(object):

    def __init__(self, match_word: str, match_lemma: Union[str, None],
                 match_index: int, impact_term: str,
                 impact_term_type: str, impact_type: str,
                 doc_id: str, sentence_index: int, sentence: str):
        self.match_word = match_word
        self.match_lemma = match_lemma
        self.match_index = match_index
        self.impact_term = impact_term
        self.impact_term_type = impact_term_type
        self.impact_type = impact_type
        self.condition_matches: List[ConditionMatch] = []
        self.doc_id = doc_id
        self.sentence_index = sentence_index
        self.sentence = sentence

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    @property
    def json(self):
        return {
            'match_word': self.match_word,
            'match_lemma': self.match_lemma,
            'match_index': self.match_index,
            'impact_term': self.impact_term,
            'impact_type': self.impact_type,
            'impact_term_type': self.impact_term_type,
            'condition_match': [match.json for match in self.condition_matches],
            'doc_id': self.doc_id,
            'sentence_index': self.sentence_index,
            'sentence': self.sentence
        }


class ConditionMatch:

    def __init__(self, match_word, match_lemma, match_index, condition_term, condition_group):
        self.match_word = match_word
        self.match_lemma = match_lemma
        self.match_index = match_index
        self.condition_term = condition_term
        self.condition_type = condition_group

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    @property
    def json(self):
        return self.__dict__


class ImpactRule(object):

    def __init__(self, impact_term: ImpactTerm, code: str, condition: str, filter_condition: str,
                 remarks: str, ignorecase: Union[None, bool] = None):
        self.impact_term = impact_term
        self.code = None if code == "" else code
        self.condition = None if condition == "" else parse_condition(condition)
        self.filter = False if filter_condition == "" else True
        self.remarks = None if remarks == "" else remarks
        self.impact_type = expand_impact_code(code)
        self.ignorecase = ignorecase

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


def read_impact_model(model_file: str, file_type: str = 'json'):
    if model_file.endswith('.json') or file_type == 'json':
        with open(model_file, 'rb') as fh:
            model_json = json.load(fh)
    elif model_file.endswith('.pcl') or file_type == 'pickle':
        with open(model_file, 'rb') as fh:
            model_json = pickle.load(fh)
    if not isinstance(model_json, dict):
        raise TypeError('model file must contain dictionary as JSON or Pickle format')
    if 'impact_rules' not in model_json.keys():
        raise TypeError('invalid impact model dictionary, property "impact_rules" is missing')
    return model_json


class ImpactModel(object):

    def __init__(self, model_file: str = None, model_json: Dict[str, any] = None,
                 add_wildcard_matches: bool = True):
        if model_file is not None:
            model_json = read_impact_model(model_file)
        self.model_json = model_json
        self.impact_rule_index = defaultdict(list)
        self.impact_group_index = defaultdict(set)
        self.impact_term_index = defaultdict(set)
        self.aspect_group_index = defaultdict(set)
        self.aspect_term_index = defaultdict(set)
        self.impact_terms: List[ImpactTerm] = []
        self.vocab: Dict[str, Set[str]] = defaultdict(set)
        self.wildcard_vocab: Dict[str, Set[str]] = defaultdict(set)
        self.added_vocab: Dict[str, Set[str]] = defaultdict(set)
        self.prefix_wildcard_lengths: Dict[int, Set[str]] = defaultdict(set)
        self.postfix_wildcard_lengths: Dict[int, Set[str]] = defaultdict(set)
        self.infix_wildcard_lengths: Dict[int, Set[str]] = defaultdict(set)
        self.prefix_vocab = defaultdict(partial(defaultdict, set))
        self.postfix_vocab = defaultdict(partial(defaultdict, set))
        self.infix_vocab = defaultdict(partial(defaultdict, set))
        self.impact_rules = [make_impact_rule(rule_json) for rule_json in model_json['impact_rules']]
        self.add_wildcard_matches = add_wildcard_matches
        self._index_impact_terms(model_json['impact_rules'])
        self.make_rule_index()
        if 'aspect_terms' in model_json:
            self._index_aspect_terms(model_json['aspect_terms'])

    def _index_impact_terms(self, impact_rules: List[Dict[str, any]]):
        """Build an index of impact terms for fast lookup."""
        found = set()
        for rule_json in impact_rules:
            if (rule_json['Impact_term'], rule_json['Impact_group']) in found:
                continue
            self._index_impact_term(rule_json)
            found.add((rule_json['Impact_term'], rule_json['Impact_group']))

    def _index_impact_term(self, term_json: Dict[str, str]) -> None:
        """Add an impact term dictionary to the model."""
        impact_term = make_impact_term(term_json)
        self.impact_terms.append(impact_term)
        self.impact_term_index[impact_term.string].add(impact_term.group)
        self.vocab[impact_term.string].add('impact_term')
        if impact_term.has_wildcard:
            self._index_wildcard_suffix(impact_term, 'impact_term')

    def _index_wildcard_suffix(self, wildcard_term: Term, term_type: str):
        self.wildcard_vocab[wildcard_term.string].add(term_type)
        wildcard_type = has_wildcard_type(wildcard_term.string)
        if wildcard_type == 'post':
            suffix = wildcard_term.string[1:]
            self.postfix_wildcard_lengths[len(suffix)].add(suffix)
        elif wildcard_type == 'pre':
            suffix = wildcard_term.string[:-1]
            self.prefix_wildcard_lengths[len(suffix)].add(suffix)
        elif wildcard_type == 'both':
            suffix = wildcard_term.string[1:-1]
            self.infix_wildcard_lengths[len(suffix)].add(suffix)
        else:
            return None
        if term_type == 'impact_term':
            self.impact_term_index[suffix].add(wildcard_term.group)
        else:
            self.aspect_term_index[suffix].add(wildcard_term.group)

    def make_rule_index(self) -> None:
        """makes an indexes of all impact rules per impact term"""
        self.impact_rule_index = defaultdict(list)
        for impact_rule in self.impact_rules:
            self.impact_rule_index[impact_rule.impact_term.string].append(impact_rule)

    def impact_term_rules(self, impact_term: str) -> Union[None, List[ImpactRule]]:
        """returns all impact rules for a given impact term"""
        if impact_term not in self.impact_rule_index:
            return None
        else:
            return self.impact_rule_index[impact_term]

    def _index_aspect_terms(self, aspect_terms_json: List[Dict[str, str]]) -> None:
        """indexes aspect terms per group and aspect groups per term"""
        for aspect_term_json in aspect_terms_json:
            term = aspect_term_json["Aspect_term"]
            group = aspect_term_json["Aspect_category"]
            self.aspect_group_index[group].add(term)
            self.aspect_term_index[term].add(group)
            aspect_term = AspectTerm(term, group)
            self.vocab[term].add('aspect_term')
            if aspect_term.has_wildcard:
                self._index_wildcard_suffix(aspect_term, 'aspect_term')

    def aspect_term(self, term: str) -> Union[None, Dict[str, Union[str, List[str]]]]:
        """returns a dictionary of an aspect term and its aspect group(s)"""
        if term not in self.aspect_term_index:
            return None
        groups = list(self.aspect_term_index[term])
        if len(groups) == 1:
            groups = groups[0]
        return {
            "aspect_term": term,
            "aspect_group": groups
        }

    def aspect_group(self, group: str) -> Union[None, Dict[str, Union[str, Set[str]]]]:
        """returns a dictionary of an aspect group and its aspect terms"""
        if group not in self.aspect_group_index:
            return None
        return {
            "aspect_term": list(self.aspect_group_index[group]),
            "aspect_group": group
        }

    def get_term_groups(self, term: str, term_type: str = None) -> Set[str]:
        if term_type and term_type not in ['aspect_term', 'impact_term']:
            raise ValueError(f'invalid term_type {term_type}, must be one of "aspect_term" or "impact_term"')
        groups = set()
        if term in self.vocab:
            vocab_terms = [term]
        else:
            vocab_terms = self.matches_wildcard_terms(term)
            # print('matches vocab_terms:', vocab_terms)
        for vocab_term in vocab_terms:
            if 'impact_term' in self.vocab[vocab_term] and term_type != 'aspect_term':
                for group in self.impact_term_index[vocab_term]:
                    groups.add(group)
            elif 'aspect_term' in self.vocab[vocab_term] and term_type != 'impact_term':
                for group in self.aspect_term_index[vocab_term]:
                    groups.add(group)
        return groups

    def matches_wildcard_terms(self, term: str) -> Set[str]:
        wildcard_terms = set()
        for i in self.postfix_wildcard_lengths:
            postfix = term[-i:]
            if postfix in self.postfix_wildcard_lengths[i]:
                wildcard_terms.add('*' + postfix)
        for i in self.prefix_wildcard_lengths:
            prefix = term[:i]
            if prefix in self.prefix_wildcard_lengths[i]:
                wildcard_terms.add(prefix + '*')
        return wildcard_terms

    def has_aspect_term(self, term: str) -> bool:
        return self.has_term(term, 'aspect_term')

    def has_impact_term(self, term: str) -> bool:
        return self.has_term(term, 'impact_term')

    def has_term(self, term: str, term_type: str) -> bool:
        """Check if model has given term with given term type.

        :param term: term to lookup in the model vocabulary
        :type term: str
        :param term_type: type of term (impact or aspect)
        :type term_type: str
        :return: whether the model has term as impact term
        :rtype: bool
        """
        if term in self.vocab:
            return term_type in self.vocab[term]
        if term in self.added_vocab:
            wildcard_terms = term_type in self.added_vocab[term]
        else:
            wildcard_terms = self.matches_wildcard_terms(term)
        for wildcard_term in wildcard_terms:
            if term_type in self.vocab[wildcard_term]:
                self.added_vocab[term].add(wildcard_term)
                return True
        return False

    def get_matching_vocab_term(self, term: str) -> Union[None, str, Set[str]]:
        if term in self.vocab:
            return term
        if term in self.added_vocab:
            return self.added_vocab[term]
        wildcard_terms = self.matches_wildcard_terms(term)
        if len(wildcard_terms) == 0:
            return None
        elif len(wildcard_terms) == 1:
            return wildcard_terms.pop()
        else:
            return wildcard_terms


def parse_phrase_wildcards(phrase: str) -> str:
    return phrase.replace("*", r"\w*")


def parse_discontinuous_phrase(phrase: str) -> str:
    """
    Transform discontinuous phrase into a regular expression. Discontinuity is
    interpreted as taking place at any whitespace outside of terms grouped by
    parentheses. That is, the whitespace indicates that anything can be in between
    the left side and right side.
    Example 1: x1 (x2 (x3"x4")) becomes x1.+(x2 (x3|x4))
    """
    level = 0
    parsed_phrase = ""
    for index, char in enumerate(phrase):
        if char == "(":
            level += 1
        elif char == ")":
            level -= 1
        elif char == " " and level == 0:
            char = ".+"
        parsed_phrase += char
    return parsed_phrase


def get_term_string(impact_term: Dict[str, str]) -> str:
    if "discontinuous" in impact_term["Impact_group"]:
        impact_term["Impact_term"] = parse_discontinuous_phrase(impact_term["Impact_term"])
    return impact_term["Impact_term"]


def get_term_group(impact_term: Dict[str, str]) -> str:
    return impact_term["Impact_group"]


def get_term_type(impact_term: Dict[str, str]) -> str:
    if "phrase" in get_term_group(impact_term):
        return "phrase"
    elif impact_term["Impact_term"].startswith('(') and impact_term["Impact_term"].endswith(')'):
        return "regex"
    else:
        return "term"


def get_term_pos(impact_term: Dict[str, str]) -> str:
    if "adjective" in get_term_group(impact_term):
        return "adj"
    elif "noun" in get_term_group(impact_term):
        return "noun"
    elif "adverb" in get_term_group(impact_term):
        return "adv"
    elif "verb" in get_term_group(impact_term):
        return "verb"


def make_impact_term(term_json: Dict[str, str]) -> ImpactTerm:
    return ImpactTerm(
        get_term_string(term_json),
        get_term_group(term_json),
        get_term_pos(term_json),
        get_term_type(term_json)
    )


# Conditions
# @...   Refers to group in sheet of book aspects
# %(...) Continuous group must be present in neighbourhood
# %...   Word must be present in neighbourhood
# ^...   Word must be present at start of sentence
# #(...) discontinuous group must be present in neighbourhood

def parse_condition(condition_string: str) -> Dict[str, str]:
    """parses coded condition of impact rule to more readable json"""
    condition_symbol = condition_string[0]
    condition_term = condition_string[1:]
    condition = {
        "condition_type": "context_term",
        "context_term": condition_term,
        "term_type": "term",
        "location": "neighbourhood"
    }
    if condition_symbol == "@":
        condition["condition_type"] = "aspect_term"
        del condition["context_term"]
        condition["aspect_group"] = condition_term
    elif condition_symbol == "%":
        condition["location"] = "neighbourhood"
        if condition_term[0] == "(" and condition_term[-1] == ")":
            condition["term_type"] = "phrase"
            condition["phrase_type"] = "continuous"
    elif condition_symbol == "^":
        condition["location"] = "sentence_start"
    elif condition_symbol == "$":
        condition["location"] = "sentence_end"
    elif condition_symbol == "#":
        if condition_term[0] == "(" and condition_term[-1] == ")":
            condition["context_term"] = condition["context_term"][1:-1]
        condition["term_type"] = "phrase"
        condition["phrase_type"] = "discontinuous"
        condition["context_term"] = parse_discontinuous_phrase(condition["context_term"])
    if condition["term_type"] == "phrase":
        condition["context_term"] = parse_phrase_wildcards(condition["context_term"])
    return condition


def expand_impact_code(code: str) -> Union[None, str]:
    """map impact code to readable impact type"""
    if code == "A":
        return "Affect"
    if code == "Att":
        return "Attention"
    if code == "H":
        return "Humor"
    if code == "N":
        return "Narrative"
    if code == "R":
        return "Reflection"
    if code == "S":
        return "Style"
    if code == "Sur":
        return "Surprise"
    if code == "Neg":
        return "Negative"
    if code == "Neu":
        return "Neutral"
    else:
        return None


def make_impact_rule(rule_json: dict) -> ImpactRule:
    impact_term = ImpactTerm(get_term_string(rule_json), get_term_group(rule_json),
                             get_term_pos(rule_json), get_term_type(rule_json))
    ignorecase = rule_json["Ignore case"] if "Ignore case" in rule_json else True
    return ImpactRule(
        impact_term,
        rule_json["Category"],
        rule_json["Condition"],
        rule_json["Neg-filter"],
        rule_json["Comments"],
        ignorecase
    )


def make_aspect_term(aspect_term_json: Dict[str, str]) -> AspectTerm:
    return AspectTerm(aspect_term_json["Aspect_term"], aspect_term_json["Aspect_category"])


def import_model(lang: str):
    # solution from:
    # https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package
    try:
        import importlib.resources as pkg_resources
    except ImportError:
        # Try backported to PY<37 `importlib_resources`.
        import importlib_resources as pkg_resources

    # relative-import the *package* containing the models
    from . import models

    if lang == 'en':
        model_file = 'impact_model-en.json'
    elif lang == 'nl':
        model_file = 'impact_model-nl.json'
    else:
        raise ValueError(f'unknown language option "{lang}", must be one of ["en", "nl"]')
    model_json_string = pkg_resources.read_text(models, model_file)
    return json.loads(model_json_string)


def load_model(lang: str = 'en', model_file: str = None) -> ImpactModel:
    """Load an impact model from a json or a pickle file."""
    if not model_file:
        # if no model_file is given, load one for the specified language
        model_json = import_model(lang)
        return ImpactModel(model_json=model_json)
    with open(model_file, 'rb') as fh:
        impact_model = pickle.load(fh)
        if not isinstance(impact_model, ImpactModel):
            raise TypeError(f'{model_file} does not contain an ImpactModel')
        return impact_model
