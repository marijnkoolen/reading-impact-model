from __future__ import annotations
import re
from typing import Dict, List, Set, Tuple, Union


class ImpactPhraseSpan:

    def __init__(self, phrase_string: str, start: int, end: int, span_type: str):
        self.phrase_string = phrase_string
        if not isinstance(start, int):
            raise TypeError('start value must be integer')
        if not isinstance(end, int):
            raise TypeError('end value must be integer')
        if start < 0:
            raise ValueError('start offset must be positive')
        if end <= start:
            raise ValueError('end offset must be higher than start offset')
        self.start = start
        self.end = end
        self.range = (start, end)
        self.children: List[ImpactPhraseSpan] = []
        self.parent: Union[None, ImpactPhraseSpan] = None
        self.type: str = span_type

    def __repr__(self):
        return f'{self.__class__.__name__}(type={self.type}, range={self.range}, string="{self.phrase_string}")'

    def __gt__(self, other: ImpactPhraseSpan):
        return self.start > other.start

    def __ge__(self, other: ImpactPhraseSpan):
        return self.start >= other.start

    def __lt__(self, other: ImpactPhraseSpan):
        return self.start < other.start

    def __le__(self, other: ImpactPhraseSpan):
        return self.start <= other.start

    def __eq__(self, other: ImpactPhraseSpan):
        return self.start == other.start and self.end == other.end


class ImpactSpanTree:

    def __init__(self, phrase: str, spans: List[ImpactPhraseSpan]):
        self.phrase: str = phrase
        self.root: Union[None, ImpactPhraseSpan] = None
        self.leaves: Set[ImpactPhraseSpan] = set()
        self.spans: List[ImpactPhraseSpan] = spans
        for span in spans:
            if span.parent is None:
                self.root = span
            if len(span.children) == 0:
                self.leaves.add(span)


class ImpactPhrase:

    def __init__(self, phrase: str):
        self.phrase = phrase


def is_phrase_group(phrase_string: str) -> bool:
    if phrase_string[0] != '(':
        return False
    if phrase_string[-1] != ')':
        return False
    return True


def split_group(group_span: ImpactPhraseSpan,
                group_index: Dict[Tuple[int, int], ImpactPhraseSpan]) -> List[ImpactPhraseSpan]:
    child_spans: List[ImpactPhraseSpan] = []
    split_char = '|' if group_span.type == 'alt_group' else ' '
    if is_phrase_group(group_span.phrase_string):
        # phrase has grouping parentheses
        split_string = group_span.phrase_string[1:-1]
        start = group_span.start + 1
    else:
        split_string = group_span.phrase_string
        start = group_span.start
    parts = split_string.split(split_char)
    for part in parts:
        if part[0] == '<' and part[-1] == '>':
            start, end = [int(offset) for offset in part.replace('<span_', '').replace('>', '').split(':')]
            child_span = group_index[(start, end)]
        else:
            end = start + len(part)
            child_span = ImpactPhraseSpan(part, start, end, span_type='term')
        child_spans.append(child_span)
        start = end + 1
    return child_spans


def replace_inner_groups(phrase: str) -> Dict[str, Union[str, Dict[Tuple[int, int], ImpactPhraseSpan]]]:
    group_index = {}
    child_spans = []
    phrase_copy = phrase
    for match in re.finditer(r'\([^\(].*?\)', phrase):
        span_type = 'alt_group' if '|' in match.group() else 'seq_group'
        group_span = ImpactPhraseSpan(match.group(), match.span()[0], match.span()[1], span_type=span_type)
        group_index[match.span()] = group_span
        child_spans.append(group_span)
    for span_range in sorted(group_index.keys(), reverse=True):
        phrase_copy = phrase_copy[:span_range[0]] + f'<span_{span_range[0]}:{span_range[1]}>' + phrase_copy[
                                                                                                span_range[1]:]
    return {'phrase': phrase_copy, 'group_index': group_index}


def index_groups(phrase: str) -> Dict[Tuple[int, int], ImpactPhraseSpan]:
    group_index = {}
    phrase_copy = phrase
    loop_count = 0
    while '(' in phrase and ')' in phrase_copy:
        result = replace_inner_groups(phrase_copy)
        for span_range in result['group_index']:
            group_index[span_range] = result['group_index'][span_range]
        phrase_copy = result['phrase']
        loop_count += 1
    if ' ' in phrase_copy:
        phrase_span = ImpactPhraseSpan(phrase_copy, 0, len(phrase), span_type='seq_group')
        group_index[phrase_span.range] = phrase_span
    return group_index


def build_span_tree(phrase: str) -> ImpactPhraseSpan:
    group_index = index_groups(phrase)
    root_range = (0, len(phrase))
    for span_range in group_index:
        group = group_index[span_range]
        child_spans = split_group(group, group_index)
        for child_span in child_spans:
            child_span.parent = group
            group.children.append(child_span)
    root = group_index[root_range]
    return root  # ImpactSpanTree(phrase, group_index.values())


def run_main():
    test_phrase = 'this (sentence|text) has (a|one|some|multiple) (phrase|phrases) ' + \
                  '((some|a few) (of which are|which are) nested)'
    root_span = build_span_tree(test_phrase)
    print(root_span)
    for child_span in root_span.children:
        print('\t', child_span)
        for grandchild_span in child_span.children:
            print('\t\t', grandchild_span)


if __name__ == "__main__":
    run_main()
