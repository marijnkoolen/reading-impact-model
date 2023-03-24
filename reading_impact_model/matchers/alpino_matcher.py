#!/usr/local/bin/python
import re
import json
from typing import Dict, List, Union
from xml.parsers.expat import ExpatError

import xmltodict

import reading_impact_model.matchers.matcher as matcher
from reading_impact_model.impact_model import ImpactModel


def remove_trailing_punctuation(string: str) -> str:
    """removes leading and trailing punctuation from a string. Needed for Alpino word nodes"""
    return re.sub(r"^\W*\b(.*)\b\W*$", r"\1", string)


def clean_word_node(node: dict) -> None:
    """clean punctuation from Alpino word nodes (lemma and surface word)"""
    node["@word"] = remove_trailing_punctuation(node["@word"])
    node["@lemma"] = remove_trailing_punctuation(node["@lemma"])


def get_word_nodes(node: dict) -> List[dict]:
    """parse the top node of an Alpino parse and return all the leave nodes in sentence order"""
    if isinstance(node, list):
        return [descendent for child_node in node for descendent in get_word_nodes(child_node)]
    elif "node" in node and isinstance(node["node"], list):
        return [descendent for child_node in node["node"] for descendent in get_word_nodes(child_node)]
    elif "node" in node:
        return get_word_nodes(node["node"])
    elif "@word" in node:
        clean_word_node(node)
        return [node]
    else:
        return []


class AlpinoError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def is_alpino_xml_string(string: str) -> bool:
    if not isinstance(string, str):
        return False
    try:
        validate_alpino_ds(string)
        return True
    except ExpatError:
        return False


def validate_alpino_ds(alpino_ds: Union[str, dict]):
    """check that the given alpino parse is a valid alpino parse."""
    if isinstance(alpino_ds, str):
        """Try and parse variable as XML string"""
        try:
            xml_dict = xmltodict.parse(alpino_ds)
            alpino_ds = xml_dict['alpino_ds']
        except KeyError:
            raise AlpinoError('Invalid Alpino XML string, root element must be "alpino_ds"')
    if not isinstance(alpino_ds, dict):
        raise AlpinoError("alpino_ds must be an Alpino XML string or a JSON representation of Alpino XML output")
    required_fields = ["@version", "parser", "node", "sentence"]
    for required_field in required_fields:
        if required_field not in alpino_ds.keys():
            print(json.dumps(alpino_ds, indent=2))
            raise AlpinoError("alpino_ds is not a valid JSON representation of Alpino XML output")


class AlpinoSentence(object):

    def __init__(self, alpino_ds):
        # TO DO: accept and parse Alpino XML doc and string as input
        validate_alpino_ds(alpino_ds)
        self.word_nodes = get_word_nodes(alpino_ds["node"])
        self.sentence_string = alpino_ds["sentence"]["#text"]
        self.alpino_ds = alpino_ds


def check_alpino_sentence(alpino_sentence: Union[str, AlpinoSentence]) -> bool:
    """Check that either a new valid alpino sentence is given or that a valid alpino sentence is already set."""
    if isinstance(alpino_sentence, AlpinoSentence):
        return True
    try:
        AlpinoSentence(alpino_sentence)
        return True
    except ValueError:
        return False


class AlpinoMatcher(matcher.ImpactMatcher):

    def __init__(self, parser, lang: str = 'en', impact_model: ImpactModel = None,
                 **kwargs):
        super().__init__(lang=lang, impact_model=impact_model, **kwargs)
        self.parser = parser
        self.lang = lang

    def _iter_text_sentences(self, text: str):
        doc = self.parser(text)
        for sent in doc.sents:
            self._set_sentence(sent)
            yield sent

    def _set_sentence(self, sentence: Union[str, AlpinoSentence]) -> None:
        self._reset_sentence()
        if isinstance(sentence, str) and is_alpino_xml_string(sentence):
            sentence = AlpinoSentence(sentence)
        self.sentence_string = sentence.sentence_string
        for word_node in sentence.word_nodes:
            token = {
                'word': word_node['@word'],
                'lemma': word_node['@lemma'],
                'pos': word_node['@pos']
            }
            self.sentence_tokens.append(token)
            self.add_candidate_rules(token['word'], token['lemma'])

    def analyse_text(self, text: str) -> Dict[str, any]:
        all_matches = []
        for sentence in self._iter_text_sentences(text):
            self._set_sentence(sentence)
            sentence_matches = self._match_rules()
            all_matches.extend(sentence_matches)
        review_impact = self.compute_review_impact(all_matches)
        return review_impact
