from collections import defaultdict
import pickle

class ImpactModel(object):

    def __init__(self, impact_terms_json, impact_rules_json, aspect_terms_json):
        self.impact_terms = [make_impact_term(term_json) for term_json in impact_terms_json]
        self.impact_rules = [make_impact_rule(rule_json) for rule_json in impact_rules_json]
        self.make_rule_index()
        self.index_aspect_terms(aspect_terms_json)

    def make_rule_index(self):
        """makes an indexes of all impact rules per impact term"""
        self.impact_rule_index = defaultdict(list)
        for impact_rule in self.impact_rules:
            self.impact_rule_index[impact_rule.impact_term.string].append(impact_rule)

    def impact_term_rules(self, impact_term):
        """returns all impact rules for a given impact term"""
        if impact_term not in self.impact_rule_index:
            return None
        else:
            return self.impact_rule_index[impact_term]

    def index_aspect_terms(self, aspect_terms_json):
        """indexes aspect terms per group and aspect groups per term"""
        self.aspect_group_index = defaultdict(dict)
        self.aspect_term_index = defaultdict(dict)
        for aspect_term_json in aspect_terms_json:
            term = aspect_term_json["Aspect_term"]
            group = aspect_term_json["Aspect_category"]
            self.aspect_group_index[group][term] = 1
            self.aspect_term_index[term][group] = 1

    def aspect_term(self, term):
        """returns a dictionary of an aspect terms and its aspect group(s)"""
        if term not in self.aspect_term_index:
            return None
        groups = self.aspect_term_index[term].keys()
        if len(groups) == 1:
            groups = groups[0]
        return {
            "aspect_term": term,
            "aspect_group": groups
        }

    def aspect_group(self, group):
        """returns a dictionary of an aspect group and its aspect terms"""
        if group not in self.aspect_group_index:
            return None
        return {
            "aspect_term": self.aspect_group_index[group].keys(),
            "aspect_group": group
        }

class ImpactTerm(object):

    def __init__(self, impact_string, impact_group, string_pos, group_type):
        self.string = impact_string
        self.group = impact_group
        self.pos = string_pos
        self.type = group_type

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class AspectTerm(object):

    def __init__(self, term, category):
        self.string = term
        self.category = category

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class ImpactRule(object):

    def __init__(self, impact_term, code, condition, filter_condition, remarks, ignorecase=None):
        self.impact_term = impact_term
        self.code = None if code == "" else code
        self.condition = None if condition == "" else parse_condition(condition)
        self.filter = False if filter_condition == "" else True
        self.remarks = None if remarks == "" else remarks
        self.impact_type = expand_impact_code(code)
        self.ignorecase = ignorecase

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

def parse_phrase_wildcards(phrase):
    return phrase.replace("*", r"\w*")

def parse_discontinuous_phrase(phrase):
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

def term_string(impact_term):
    if "discontinuous" in impact_term["Impact_group"]:
        impact_term["Impact_term"] = parse_discontinuous_phrase(impact_term["Impact_term"])
    return impact_term["Impact_term"]

def term_group(impact_term):
    return impact_term["Impact_group"]

def term_type(impact_term):
    if "phrase" in term_group(impact_term):
        return "phrase"
    else:
        return "term"

def term_pos(impact_term):
    if "adjective" in term_group(impact_term):
        return "adj"
    elif "noun" in term_group(impact_term):
        return "noun"
    elif "adverb" in term_group(impact_term):
        return "adv"
    elif "verb" in term_group(impact_term):
        return "verb"

def make_impact_term(term_json):
    return ImpactTerm(
        term_string(term_json),
        term_group(term_json),
        term_pos(term_json),
        term_type(term_json)
    )

# Conditions
# @...   Refers to group in sheet of book aspects
# %(...) Continuous group must be present in neighbourhood
# %...   Word must be present in neighbourhood
# ^...   Word must be present at start of sentence
# #(...) discontinuous group must be present in neighbourhood

def parse_condition(condition_string):
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
        condition["aspect_group"] =  condition_term
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

def expand_impact_code(code):
    """map impact code to readable impact type"""
    if code == "R":
        return "Reflection"
    if code == "A":
        return "Affect"
    if code == "N":
        return "Narrative"
    if code == "S":
        return "Style"
    else:
        return None

def make_impact_rule(rule_json):
    rule_fields = ["Impact_group", "Impact_term", "Code as", "Condition", "neg filter*", "remarks"]
    impact_term = ImpactTerm(term_string(rule_json), term_group(rule_json), term_pos(rule_json), term_type(rule_json))
    ignorecase = rule_fields["Ignore case"] if "Ignore case" in rule_fields else True
    return ImpactRule(
        impact_term,
        rule_json["Code as"],
        rule_json["Condition"],
        rule_json["neg filter*"],
        rule_json["remarks"],
        ignorecase
    )

def make_aspect_term(aspect_term_json):
    return AspectTerm(aspect_term_json["Aspect_term"], aspect_term_json["Aspect_category"])

def load_model(model_file):
    """Load an impact model from a pickle file."""
    with open(model_file, 'rb') as fh:
        return pickle.load(fh)

