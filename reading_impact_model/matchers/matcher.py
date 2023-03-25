import re
from collections import defaultdict
from typing import Dict, List, Union

from nltk.tokenize import sent_tokenize

from reading_impact_model.impact_model import ImpactModel, ImpactRule, ImpactMatch, ConditionMatch, Token
from reading_impact_model.impact_model import IMPACT_TYPES, IMPACT_MATCH_FIELDS, CONDITION_MATCH_FIELDS
from reading_impact_model.impact_model import load_model
from reading_impact_model.impact_model import is_wildcard_term, wildcard_term_match


def map_review_impact(match):
    if match['impact_type'] == 'Affect':
        return 'positive'
    else:
        return match['impact_type'].lower()


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
        self.lang = lang
        if lang is not None:
            self.impact_model = load_model(lang=lang)
        elif isinstance(impact_model, ImpactModel):
            self.impact_model = impact_model
        else:
            raise TypeError("Matcher must be instantiated with an ImpactModel object")
        self.debug = debug
        self.sentence_string = ''
        self.sentence_tokens = []
        self.doc_id = None
        self.sentence_index = None
        self.sentence_vocab_terms = defaultdict(set)
        self.sentence_impact_terms = set()
        self.sentence_aspect_terms = set()
        self.candidate_rules = defaultdict(int)
        self.impact_rule_term_index = defaultdict(list)
        self._index_impact_rule_words()

    def _index_impact_rule_string(self, string: str, rule: ImpactRule, term_type: str):
        if term_type == 'term':
            self.impact_rule_term_index[string] += [rule]
        elif term_type == 'phrase' or term_type == 'regex':
            try:
                for phrase_part in string.strip().split(' '):
                    if phrase_part[0] == '(' and phrase_part[-1] == ')':
                        phrase_part_terms = re.split(r'[ |]', phrase_part[1:-1])
                        # phrase_part_terms = phrase_part[1:-1].split('|')
                        for term in phrase_part_terms:
                            self.impact_rule_term_index[term] += [rule]
                    else:
                        self.impact_rule_term_index[phrase_part] += [rule]
            except IndexError:
                print(string)
                print(string.split(' '))
                raise

    def _index_impact_rule_words(self):
        for rule in self.impact_model.impact_rules:
            self._index_impact_rule_string(rule.impact_term.string, rule, rule.impact_term.type)
            # print(rule.condition)
            # if rule.condition and rule.condition['context_term']:
            #     self._index_impact_rule_string(rule.condition['context_term'], rule, rule.condition['term_type'])

    def add_candidate_rules(self, token, lemma):
        # print('token:', token)
        if token in self.impact_rule_term_index:
            # print('\tin term index')
            for rule in self.impact_rule_term_index[token]:
                # print('\tadding rule', rule)
                self.candidate_rules[rule] += 1
        if lemma != token and lemma in self.impact_rule_term_index:
            for rule in self.impact_rule_term_index[lemma]:
                self.candidate_rules[rule] += 1

    def _add_sentence_token(self, token: Token):
        self.sentence_tokens.append(token)
        vocab_terms = self.impact_model.get_matching_vocab_term(token.word)
        if isinstance(vocab_terms, str):
            self.sentence_vocab_terms[vocab_terms].add(token)
        elif isinstance(vocab_terms, set):
            for vocab_term in vocab_terms:
                self.sentence_vocab_terms[vocab_term].add(token)
        if token.lemma == token.word:
            return None
        vocab_terms = self.impact_model.get_matching_vocab_term(token.lemma)
        if isinstance(vocab_terms, str):
            self.sentence_vocab_terms[vocab_terms].add(token)
        elif isinstance(vocab_terms, set):
            for vocab_term in vocab_terms:
                self.sentence_vocab_terms[vocab_term].add(token)

    def _set_dict_sentence(self, sentence_index: int, sentence: Dict[str, any], doc_id: str) -> None:
        self.sentence_string = sentence['text']
        self.sentence_id = (sentence_index, doc_id)
        for ti, token in enumerate(sentence['tokens']):
            token = Token(word=token.word, index=ti, lemma=token.lemma, pos=token.pos if 'pos' in token else None)
            self._add_sentence_token(token)
            self.add_candidate_rules(token.word, token.lemma)

    def _set_string_sentence(self, sentence_index: int, sentence: str, doc_id: str) -> None:
        self.sentence_string = sentence
        self.sentence_id = (sentence_index, doc_id)
        words = re.split(r'\W+', sentence)
        for wi, word in enumerate(words):
            token = Token(word, wi, lemma=word)
            self._add_sentence_token(token)
            self.add_candidate_rules(word, word)
        # print('sentence_string:', self.sentence_string)
        # print('sentence_tokens:', self.sentence_tokens)

    def _reset_sentence(self):
        self.sentence_string = ''
        self.sentence_tokens = []
        self.sentence_vocab_terms = defaultdict(set)
        self.candidate_rules = defaultdict(int)
        self.sent_id = None

    def _set_sentence(self, sentence_index: int, sentence: str, doc_id: str) -> None:
        self._reset_sentence()
        self.doc_id = doc_id
        if isinstance(sentence, dict) and 'text' in sentence and 'tokens' in sentence:
            self._set_dict_sentence(sentence_index, sentence, doc_id)
        elif isinstance(sentence, str):
            self._set_string_sentence(sentence_index, sentence, doc_id)
        else:
            raise TypeError(
                "sentence must be either a string, an Sentence object from Alpino, Spacy or Stanza.")

    def _iter_text_sentences(self, text: str, doc_id: str = None):
        for si, sent in enumerate(sent_tokenize(text)):
            self._set_sentence(si, sent, doc_id)
            yield si

    def analyse_text(self, text: str, doc_id: str = None,
                     include_neutral: bool = False) -> List[Dict[str, any]]:
        all_matches = []
        for _ in self._iter_text_sentences(text, doc_id):
            sentence_matches = self._match_rules()
            all_matches.extend(sentence_matches)
        review_impact = self.compute_review_impact(all_matches,
                                                   include_neutral=include_neutral)
        return review_impact

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
        match_tokens = self.sentence_vocab_terms[match_term] if match_term in self.sentence_vocab_terms else []
        for token in match_tokens:
            if ignorecase:
                word = token.word.lower()
                match_term = match_term.lower()
            else:
                word = token.word
            if term_match(word, match_term):
                yield token

    def get_sentence_lemmas_matching_term(self, match_term, match_pos, ignorecase=True):
        if self.debug:
            print("looking for lemmas matching term:", match_term, match_pos)
            print(self.sentence_vocab_terms)
            print(match_term in self.sentence_vocab_terms)
        match_tokens = self.sentence_vocab_terms[match_term] if match_term in self.sentence_vocab_terms else []
        for token in match_tokens:
            if ignorecase:
                lemma = token.lemma.lower()
                word = token.word.lower()
                match_term = match_term.lower()
            else:
                lemma = token.lemma
                word = token.word
            if self.debug:
                print("\tlemma:", token.lemma, "pos:", token.pos)
            # CHANGED 2020-06-18: also check if match term matches the word in the sentence, not just the lemma
            # matching either is good enough
            if not term_match(lemma, match_term) and not term_match(word, match_term):
                continue
            if not match_pos or not token.pos or token.pos == match_pos or token.pos == "name":
                if self.debug:
                    print("MATCH OF LEMMA AND POS!")
                yield token
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
        self._set_sentence(sentence)
        return self._match_rules()

    def _match_rules(self):
        """Match sentence against all impact rules of the impact model."""
        return [match for impact_rule in self.candidate_rules for match in self.match_rule(impact_rule)]

    def match_rule(self, impact_rule: ImpactRule, sentence=None) -> List[ImpactMatch]:
        """Match sentence against a specific impact rule."""
        if sentence:
            if self.debug:
                print('setting sentence for single rule match')
            self._set_sentence(sentence)
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
                                       impact_rule.impact_term.type, impact_rule.impact_type,
                                       doc_id=self.doc_id, sentence_index=self.sentence_index,
                                       sentence=self.sentence_string)
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
        for impact_token in self.get_sentence_lemmas_matching_term(match_term, match_pos,
                                                                   ignorecase=impact_rule.ignorecase):
            impact_match = ImpactMatch(impact_token.word, impact_token.lemma, impact_token.index,
                                       impact_rule.impact_term.string, impact_rule.impact_term.type,
                                       impact_rule.impact_type,
                                       doc_id=self.doc_id, sentence_index=self.sentence_index,
                                       sentence=self.sentence_string)
            if self.debug:
                print("match term:", impact_token.word)
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
            for aspect_match in self.get_sentence_words_matching_term(aspect_term,
                                                                      ignorecase=impact_rule.ignorecase):
                condition_match = ConditionMatch(aspect_match.word, aspect_match.lemma, aspect_match.index,
                                                 aspect_term, aspect_group)
                condition_matches.append(condition_match)
            if len(condition_matches) > 0:
                impact_match.condition_matches = condition_matches
                return True
            for aspect_token in self.get_sentence_lemmas_matching_term(aspect_term, None,
                                                                       ignorecase=impact_rule.ignorecase):
                condition_match = ConditionMatch(aspect_token.word, aspect_token.lemma, aspect_token.index,
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

    def init_impact_scores(self, match: ImpactMatch) -> Dict[str, int]:
        impact = {
            "doc_id": match.doc_id,
            "sentence_index": match.sentence_index,
            "sentence": match.sentence,
        }
        for impact_type in IMPACT_TYPES[self.lang]:
            impact[impact_type] = 0
        for field in IMPACT_MATCH_FIELDS:
            impact[field] = match.__getattribute__(field)
        for cond_field in CONDITION_MATCH_FIELDS:
            if len(match.condition_matches) > 0:
                display_field = cond_field if cond_field.startswith('cond') else f'condition_{cond_field}'
                impact[display_field] = match.condition_matches[0].__getattribute__(cond_field)
        return impact

    def compute_review_impact(self, impact_matches: List[ImpactMatch],
                              include_neutral: bool = False) -> List[Dict[str, any]]:
        positive_sub_cat = {'style', 'narrative', 'humor'}
        review_impact = []
        counted = set()
        for match in impact_matches:
            impact = self.init_impact_scores(match)
            if include_neutral is False and match.impact_type == 'Neutral':
                continue
            match = match.json
            for field in IMPACT_MATCH_FIELDS:
                impact[field] = match[field]
            for cond_field in CONDITION_MATCH_FIELDS:
                if 'condition_match' in match and len(match['condition_match']) > 0:
                    display_field = cond_field if cond_field.startswith('cond') else f'condition_{cond_field}'
                    impact[display_field] = match['condition_match'][0][cond_field]
            if match['impact_type'] == 'Neutral':
                continue
            impact_type = map_review_impact(match)
            if (match['match_index'], impact_type) not in counted:
                impact[impact_type] += 1
                counted.add((match['match_index'], impact_type))
            if impact_type in positive_sub_cat:
                if (match['match_index'], 'positive') not in counted:
                    impact['positive'] += 1
                    counted.add((match['match_index'], 'positive'))
            review_impact.append(impact)
        return review_impact

