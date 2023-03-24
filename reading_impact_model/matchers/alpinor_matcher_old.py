import re

from reading_impact_model.matchers.alpino_matcher import AlpinoSentence, AlpinoError
from reading_impact_model.matchers.matcher import ImpactModel, term_match

class AlpinoMatcher(object):

    def __init__(self, impact_model, alpino_sentence=None, debug=False):
        if not impact_model or not isinstance(impact_model, ImpactModel):
            raise AlpinoError("AlpinoMatcher must be instantiated with an ImpactModel object")
        self.impact_model = impact_model
        self.debug = debug
        if alpino_sentence:
            self.set_alpino_sentence(alpino_sentence)
        else:
            self.alpino_sentence = None

    def set_alpino_sentence(self, alpino_sentence):
        if isinstance(alpino_sentence, AlpinoSentence):
            self.alpino_sentence = alpino_sentence
        elif isinstance(alpino_sentence, dict):
            self.alpino_sentence = AlpinoSentence(alpino_sentence)
        else:
            raise AlpinoError(
                "alpino_sentence must be an AlpinoSentence object or a JSON representation of Alpino XML output")

    def term_sentence_match(self, term, word_boundaries=True):
        """
        check if term occurs in sentence string.
        Assumes word boundaries \bterm\b by default.
        Use word_boundaries=False for pure string match
        """
        if word_boundaries:
            return re.search(r"\b" + term + r"\b", self.alpino_sentence.sentence_string)
        else:
            return term in self.alpino_sentence.sentence_string

    def get_sentence_words_matching_term(self, match_term, ignorecase=True):
        for word_index, word_node in enumerate(self.alpino_sentence.word_nodes):
            word = word_node["@word"]
            if ignorecase:
                word = word.lower()
                match_term = match_term.lower()
            if term_match(word, match_term):
                yield word_index, word_node

    def get_sentence_lemmas_matching_term(self, match_term, match_pos, ignorecase=True):
        if self.debug:
            print("looking for lemmas matching term:", match_term, match_pos)
        for word_index, word_node in enumerate(self.alpino_sentence.word_nodes):
            if self.debug:
                print("lemma:", word_node["@lemma"], "pos:", word_node["@pos"])
            lemma = word_node["@lemma"]
            if ignorecase:
                lemma = lemma.lower()
                match_term = match_term.lower()
            if not term_match(lemma, match_term):
                continue
            if not match_pos or word_node["@pos"] == match_pos or word_node["@pos"] == "name":
                if self.debug:
                    print("MATCH OF LEMMA AND POS!")
                yield word_index, word_node
            elif self.debug:
                print("MATCH OF LEMMA BUT NOT OF POS!")
                print(word_node["@pos"])

    def get_sentence_string_matching_term(self, match_term, location="neighbourhood", ignorecase=True):
        if self.debug:
            print("looking for sentence string matching phrase:", match_term, "and location", location)
        sentence = self.alpino_sentence.sentence_string
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
        for match in re.finditer(match_string, self.alpino_sentence.sentence_string.lower()):
            yield match

    def check_alpino_sentence(self, alpino_sentence):
        """Check that either a new valid alpino sentence is given or that a valid alpino sentence is already set."""
        if alpino_sentence:
            self.set_alpino_sentence(alpino_sentence)
        elif not self.alpino_sentence:
            raise AlpinoError("match_rules requires an alpino_sentence")

    def match_rules(self, alpino_sentence=None):
        """Match alpino_sentence against all impact rules of the impact model."""
        self.check_alpino_sentence(alpino_sentence)
        return [match for impact_rule in self.impact_model.impact_rules for match in self.match_rule(impact_rule)]

    def match_rule(self, impact_rule, alpino_sentence=None):
        """Match alpino_sentence against a specific impact rule."""
        self.check_alpino_sentence(alpino_sentence)
        if impact_rule.impact_term.type == "phrase":
            return self.match_impact_phrase(impact_rule)
        else:
            return self.match_impact_term(impact_rule)

    def match_impact_phrase(self, impact_rule):
        matches = []
        if self.debug:
            print("match_phrase:", impact_rule.impact_term.string)
            print("impact_term:", impact_rule.impact_term)
            print("sentence:", self.alpino_sentence.sentence_string)
        for match in self.get_sentence_string_matching_term(impact_rule.impact_term.string,
                                                            ignorecase=impact_rule.ignorecase):
            match = {
                "match_term_offset": match.start(),
                "match_term": match.group(0),
                "impact_term": impact_rule.impact_term.string,
                "impact_term_type": impact_rule.impact_term.type,
                "impact_type": impact_rule.impact_type
            }
            if self.match_condition(impact_rule, match):
                matches.append(match)
            elif self.debug:
                print("PHRASE CONDITION NOT MET:", impact_rule.condition)
        return matches

    def match_impact_term(self, impact_rule):
        matches = []
        match_term = impact_rule.impact_term.string
        match_pos = impact_rule.impact_term.pos
        if self.debug:
            print("match_term:", match_term, "match_pos:", match_pos)
            print("sentence:", self.alpino_sentence.sentence_string)
        for impact_index, impact_node in self.get_sentence_lemmas_matching_term(match_term, match_pos,
                                                                                ignorecase=impact_rule.ignorecase):
            match = {
                "match_term": impact_node["@word"],
                "match_lemma": impact_node["@lemma"],
                "impact_term_index": impact_index,
                "impact_term": impact_rule.impact_term.string,
                "impact_term_type": impact_rule.impact_term.type,
                "impact_type": impact_rule.impact_type
            }
            if self.debug:
                print("match term:", impact_node["@word"])
            if self.match_condition(impact_rule, match):
                matches.append(match)
            elif self.debug:
                print("PHRASE CONDITION NOT MET:", impact_rule.condition)
        return matches

    def match_condition(self, impact_rule, impact_match):
        match = False
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

    def match_aspect_condition(self, impact_rule, impact_match):
        aspect_group = impact_rule.condition["aspect_group"]
        aspect_info = self.impact_model.aspect_group(aspect_group)
        if not aspect_info:
            print("Error - no aspect group info for aspect group:", aspect_group)
            return False
        for aspect_term in aspect_info["aspect_term"]:
            aspect_matches = []
            for aspect_index, aspect_node in self.get_sentence_words_matching_term(aspect_term,
                                                                                   ignorecase=impact_rule.ignorecase):
                aspect_match = {
                    "aspect_term_index": aspect_index,
                    "match_term": aspect_node["@word"],
                    "match_lemma": aspect_node["@lemma"],
                    "context_term": aspect_term,
                    "context_type": aspect_group
                }
                aspect_matches.append(aspect_match)
            if len(aspect_matches) > 0:
                impact_match["aspect_match"] = aspect_matches
                return True
            for aspect_index, aspect_node in self.get_sentence_lemmas_matching_term(aspect_term, None,
                                                                                    ignorecase=impact_rule.ignorecase):
                aspect_match = {
                    "context_term_index": aspect_index,
                    "match_term": aspect_node["@word"],
                    "match_lemma": aspect_node["@lemma"],
                    "context_term": aspect_term,
                    "context_type": aspect_group
                }
                aspect_matches.append(aspect_match)
            if len(aspect_matches) > 0:
                impact_match["aspect_match"] = aspect_matches
                return True
        return False

    def match_context_condition(self, impact_rule, impact_match):
        context_term = impact_rule.condition["context_term"]
        context_matches = []
        if impact_rule.condition["location"] == "sentence_start":
            if self.debug:
                print("looking for term", context_term, " with condition", impact_rule.condition)
        for match in self.get_sentence_string_matching_term(context_term, impact_rule.condition["location"],
                                                            ignorecase=impact_rule.ignorecase):
            context_match = {
                "condition_match_offset": match.start(),
                "condition_match_string": match.group(0),
                "context_term": context_term,
                "context_type": impact_rule.condition["term_type"]
            }
            if self.debug:
                print("CONTEXT CONDITION MATCH")
            context_matches.append(context_match)
        if len(context_matches) > 0:
            impact_match["context_match"] = context_matches
            return True
        else:
            return False
