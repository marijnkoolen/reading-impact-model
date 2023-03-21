import re
from collections import defaultdict
from typing import List, Union

from spacy.tokens import Span as SpacySentence
from stanza.models.common.doc import Sentence as StanzaSentence

from reading_impact_model.impact_model import ImpactModel, ImpactTerm, ImpactRule, ImpactMatch, ConditionMatch
from reading_impact_model.impact_model import load_model
from reading_impact_model.impact_model import is_wildcard_term, wildcard_term_match
from reading_impact_model.alpino_matcher import AlpinoSentence, is_alpino_xml_string


def term_match(sentence_term, model_term):
    """this function matches a model term against a sentence term,
    uses wildcards if given, otherwise exact match"""
    if is_wildcard_term(model_term):
        try:
            return wildcard_term_match(sentence_term, model_term)
        except IndexError:
            print('Invalid model_term:', model_term)
            raise
    if sentence_term == model_term:
        return True
    else:
        return False


def lemma_term_match(lemma, term):
    """this function matches a model term against a lemma from a sentence,
    uses wildcards if given, otherwise exact match"""
    if is_wildcard_term(term):
        try:
            return wildcard_term_match(lemma, term)
        except IndexError:
            print('Invalid match_term:', term)
            raise
    if lemma == term:
        return True
    else:
        return False


def remove_trailing_punctuation(string):
    """removes leading and trailing punctuation from a string. Needed for Alpino word nodes"""
    return re.sub(r"^\W*\b(.*)\b\W*$", r"\1", string)


def check_alpino_sentence(alpino_sentence: Union[str, AlpinoSentence]) -> bool:
    """Check that either a new valid alpino sentence is given or that a valid alpino sentence is already set."""
    if isinstance(alpino_sentence, AlpinoSentence):
        return True
    try:
        alpino_sentence = AlpinoSentence(alpino_sentence)
        return True
    except ValueError:
        return False


class ImpactMatcher:

    def __init__(self, lang: str = 'en', impact_model: ImpactModel = None, debug: bool = False):
        """Create a reading impact matcher object for a given reading impact model or language.

        If only a language identifier ('en' or 'nl') is passed, the default model for that
        language will be used.

        :param lang: the language for which a reading impact model should be used (default 'en', which is English).
        :type lang: str
        :param impact_model: a specific impact model, if you want to override the default model.
        :type impact_model: ImpactModel
        """
        if lang is not None:
            self.impact_model = load_model(lang=lang)
            print('lang:', lang)
            print('model:', self.impact_model)
        elif isinstance(impact_model, ImpactModel):
            self.impact_model = impact_model
        else:
            raise TypeError("Matcher must be instantiated with an ImpactModel object")
        self.debug = debug
        self.sentence_string = ''
        self.sentence_tokens = []
        self.candidate_rules = {}
        self.impact_rule_term_index = defaultdict(list)
        self.index_impact_rule_words()

    def index_impact_rule_words(self):
        for rule in self.impact_model.impact_rules:
            if rule.impact_term.type == 'term':
                self.impact_rule_term_index[rule.impact_term.string] += [rule]
            elif rule.impact_term.type == 'phrase' or rule.impact_term.type == 'regex':
                try:
                    for phrase_part in rule.impact_term.string.strip().split(' '):
                        if phrase_part[0] == '(' and phrase_part[-1] == ')':
                            phrase_part_terms = re.split(r'[ |]', phrase_part[1:-1])
                            # phrase_part_terms = phrase_part[1:-1].split('|')
                            for term in phrase_part_terms:
                                self.impact_rule_term_index[term] += [rule]
                        else:
                            self.impact_rule_term_index[phrase_part] += [rule]
                except IndexError:
                    print(rule.impact_term.string)
                    print(rule.impact_term.string. split(' '))
                    raise

    def add_candidate_rules(self, token, lemma):
        if token in self.impact_rule_term_index:
            for rule in self.impact_rule_term_index[token]:
                self.candidate_rules[rule] += 1
        if lemma != token and lemma in self.impact_rule_term_index:
            for rule in self.impact_rule_term_index[lemma]:
                self.candidate_rules[rule] += 1

    def _set_spacy_sentence(self, sentence: SpacySentence) -> None:
        self.sentence_string = sentence.text
        for spacy_token in sentence:
            token = {
                'word': spacy_token.text,
                'lemma': spacy_token.lemma_,
                'pos': spacy_token.pos_.lower()
            }
            self.sentence_tokens.append(token)
            if not spacy_token.is_stop:
                self.add_candidate_rules(spacy_token.text, spacy_token.lemma_)

    def _set_stanza_sentence(self, sentence: StanzaSentence) -> None:
        self.sentence_string = sentence.text
        for stanza_token in sentence.words:
            token = {
                'word': stanza_token.text,
                'lemma': stanza_token.lemma,
                'pos': stanza_token.pos
            }
            self.sentence_tokens.append(token)

    def _set_alpino_sentence(self, sentence: AlpinoSentence) -> None:
        self.sentence_string = sentence.sentence_string
        for word_node in sentence.word_nodes:
            token = {
                'word': word_node['@word'],
                'lemma': word_node['@lemma'],
                'pos': word_node['@pos']
            }
            self.sentence_tokens.append(token)
            self.add_candidate_rules(token['word'], token['lemma'])

    def _set_dict_sentence(self, sentence: dict) -> None:
        self.sentence_string = sentence['text']
        for token in sentence['tokens']:
            self.sentence_tokens.append(token)
            self.add_candidate_rules(token['word'], token['lemma'])

    def _set_string_sentence(self, sentence: str) -> None:
        self.sentence_string = sentence
        for word in re.split(r'\W+', sentence):
            token = {
                'word': word,
                'lemma': word,
                'pos': None
            }
            self.sentence_tokens.append(token)
            self.add_candidate_rules(word, word)
        # print('sentence_string:', self.sentence_string)
        # print('sentence_tokens:', self.sentence_tokens)

    def set_sentence(self, sentence: Union[str, SpacySentence, AlpinoSentence]) -> None:
        self.sentence_tokens = []
        # reset candidate rules dictionary
        self.candidate_rules = defaultdict(int)
        if isinstance(sentence, SpacySentence):
            self._set_spacy_sentence(sentence)
        elif isinstance(sentence, AlpinoSentence):
            self._set_alpino_sentence(sentence)
        elif isinstance(sentence, dict) and 'text' in sentence and 'tokens' in sentence:
            self._set_dict_sentence(sentence)
        elif isinstance(sentence, str) and is_alpino_xml_string(sentence):
            alpino_sentence = AlpinoSentence(sentence)
            self._set_alpino_sentence(alpino_sentence)
        elif isinstance(sentence, str):
            self._set_string_sentence(sentence)
        else:
            raise TypeError(
                "sentence must be either a string, an Sentence object from Alpino, Spacy or Stanza.")

    def term_sentence_match(self, term, word_boundaries=True):
        """
        check if term occurs in sentence string.
        Assumes word boundaries \bterm\b by default.
        Use word_boundaries=False for pure string match
        """
        if word_boundaries:
            return re.search(r"\b" + term + r"\b", self.sentence_string)
        else:
            return term in self.sentence_string

    def get_sentence_words_matching_term(self, match_term, ignorecase=True):
        for token_index, token in enumerate(self.sentence_tokens):
            if ignorecase:
                word = token['word'].lower()
                match_term = match_term.lower()
            else:
                word = token['word']
            if term_match(word, match_term):
                yield token_index, token

    def get_sentence_lemmas_matching_term(self, match_term, match_pos, ignorecase=True):
        if self.debug:
            print("looking for lemmas matching term:", match_term, match_pos)
        for token_index, token in enumerate(self.sentence_tokens):
            if ignorecase:
                lemma = token['lemma'].lower()
                word = token['word'].lower()
                match_term = match_term.lower()
            else:
                lemma = token['lemma']
                word = token['word']
            if self.debug:
                print("\tlemma:", token["lemma"], "pos:", token["pos"])
            # CHANGED 2020-06-18: also check if match term matches the word in the sentence, not just the lemma
            # matching either is good enough
            if not term_match(lemma, match_term) and not term_match(word, match_term):
                continue
            if not match_pos or not token['pos'] or token['pos'] == match_pos or token['pos'] == "name":
                if self.debug:
                    print("MATCH OF LEMMA AND POS!")
                yield token_index, token
            elif self.debug:
                print("MATCH OF LEMMA BUT NOT OF POS!")
                print(token["pos"])

    def get_sentence_string_matching_term(self, match_term, location="neighbourhood", ignorecase=True):
        if self.debug:
            print("looking for sentence string matching phrase:", match_term, "and location", location)
        sentence = self.sentence_string
        if ignorecase:
            sentence = sentence.lower()
            match_term = match_term.lower()
        if self.debug:
            print("sentence:", sentence)
        match_string = r"\b" + match_term + r"\b"
        if location == "sentence_start":
            match_string = r"^" + match_string
            if self.debug:
                print("match_string", match_string)
        elif location == "sentence_end":
            match_string = match_string + r"$"
        try:
            for match in re.finditer(match_string, sentence):
                yield match
        except re.error:
            print('match_string:', match_string)
            print('sentence:', sentence)
            raise

    def find_impact_matches(self, sentence):
        """Return all matching impact rules for a given sentence."""
        return self.match_rules(sentence=sentence)

    def match_rules(self, sentence=None):
        """Match sentence against all impact rules of the impact model."""
        self.set_sentence(sentence)
        return [match for impact_rule in self.candidate_rules for match in self.match_rule(impact_rule)]

    def match_rule(self, impact_rule: ImpactRule, sentence=None) -> List[ImpactMatch]:
        """Match sentence against a specific impact rule."""
        if sentence:
            if self.debug:
                print('setting sentence for single rule match')
            self.set_sentence(sentence)
        if impact_rule.impact_term.type == "phrase":
            return self.match_impact_phrase(impact_rule)
        if impact_rule.impact_term.type == "regex":
            return self.match_impact_phrase(impact_rule)
        else:
            return self.match_impact_term(impact_rule)

    def match_impact_phrase(self, impact_rule) -> List[ImpactMatch]:
        """Check if sentence matches impact phrase."""
        matches: List[ImpactMatch] = []
        if self.debug:
            print("match_phrase:", impact_rule.impact_term.string)
            print("impact_term:", impact_rule.impact_term)
            print("sentence:", self.sentence_string)
        for match in self.get_sentence_string_matching_term(impact_rule.impact_term.string,
                                                            ignorecase=impact_rule.ignorecase):
            impact_match = ImpactMatch(match.group(0), None, match.start(), impact_rule.impact_term.string,
                                       impact_rule.impact_term.type, impact_rule.impact_type)
            if self.match_condition(impact_rule, impact_match):
                matches.append(impact_match)
            elif self.debug:
                print("PHRASE CONDITION NOT MET:", impact_rule.condition)
        return matches

    def match_impact_term(self, impact_rule: ImpactRule):
        """Check if sentence matches impact term."""
        impact_matches: List[ImpactMatch] = []
        match_term = impact_rule.impact_term.string
        match_pos = impact_rule.impact_term.pos
        if self.debug:
            print("match_term:", match_term, "match_pos:", match_pos)
            print("sentence:", self.sentence_string)
        for impact_index, impact_token in self.get_sentence_lemmas_matching_term(match_term, match_pos,
                                                                                 ignorecase=impact_rule.ignorecase):
            impact_match = ImpactMatch(impact_token['word'], impact_token['lemma'], impact_index,
                                       impact_rule.impact_term.string, impact_rule.impact_term.type,
                                       impact_rule.impact_type)
            if self.debug:
                print("match term:", impact_token["word"])
            if self.match_condition(impact_rule, impact_match):
                impact_matches.append(impact_match)
            elif self.debug:
                print("PHRASE CONDITION NOT MET:", impact_rule.condition)
        return impact_matches

    def match_condition(self, impact_rule: ImpactRule, impact_match: ImpactMatch):
        """Check if sentence with impact term match also matches context conditions."""
        if not impact_rule.condition:
            return True
        if self.debug:
            print("condition type:", impact_rule.condition["condition_type"])
            print("condition:", impact_rule.condition)
        if impact_rule.condition["condition_type"] == "aspect_term":
            match = self.match_aspect_condition(impact_rule, impact_match)
        elif impact_rule.condition["condition_type"] == "context_term":
            match = self.match_context_condition(impact_rule, impact_match)
        else:
            if self.debug:
                print("OTHER CONDITION:", impact_rule.condition)
            return False
        if impact_rule.filter:
            if self.debug:
                print("INVERTING MATCH")
            match = not match
        if self.debug:
            if match:
                print("MATCHING CONDITION:", impact_rule.condition)
                print("IMPACT_MATCH:", impact_match)
                print()
            else:
                print("NO MATCHING CONDITION:", impact_rule.condition)
                print("IMPACT_MATCH:", impact_match)
                print()
        return match

    def match_aspect_condition(self, impact_rule: ImpactRule, impact_match: ImpactMatch) -> bool:
        """Check if sentence with impact term match also matches aspect conditions."""
        aspect_group = impact_rule.condition["aspect_group"]
        aspect_info = self.impact_model.aspect_group(aspect_group)
        if not aspect_info:
            print("Error - no aspect group info for aspect group:", aspect_group)
            return False
        for aspect_term in aspect_info["aspect_term"]:
            condition_matches = []
            for match_index, aspect_match in self.get_sentence_words_matching_term(aspect_term,
                                                                                   ignorecase=impact_rule.ignorecase):
                condition_match = ConditionMatch(aspect_match['word'], aspect_match['lemma'], match_index,
                                                 aspect_term, aspect_group)
                condition_matches.append(condition_match)
            if len(condition_matches) > 0:
                impact_match.condition_matches = condition_matches
                return True
            for match_index, aspect_match in self.get_sentence_lemmas_matching_term(aspect_term, None,
                                                                                    ignorecase=impact_rule.ignorecase):
                condition_match = ConditionMatch(aspect_match['word'], aspect_match['lemma'], match_index,
                                                 aspect_term, aspect_group)
                condition_matches.append(condition_match)
            if len(condition_matches) > 0:
                impact_match.condition_matches = condition_matches
                return True
        return False

    def match_context_condition(self, impact_rule: ImpactRule, impact_match: ImpactMatch) -> bool:
        """Check if sentence with impact term match also matches context conditions."""
        context_term = impact_rule.condition["context_term"]
        condition_matches = []
        if impact_rule.condition["location"] == "sentence_start":
            if self.debug:
                print("looking for term", context_term, " with condition", impact_rule.condition)
        for context_match in self.get_sentence_string_matching_term(context_term, impact_rule.condition["location"],
                                                                    ignorecase=impact_rule.ignorecase):
            condition_match = ConditionMatch(context_match.group(0), None, context_match.start(),
                                             context_term, impact_rule.condition['term_type'])
            if self.debug:
                print("CONTEXT CONDITION MATCH")
            condition_matches.append(condition_match)
        if len(condition_matches) > 0:
            impact_match.condition_matches = condition_matches
            return True
        else:
            return False
