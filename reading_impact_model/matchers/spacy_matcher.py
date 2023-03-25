from typing import Dict, Union

import spacy
from spacy.tokens import Span as SpacySentence

from reading_impact_model.matchers import matcher
from reading_impact_model.impact_model import ImpactModel, Token


class SpacyMatcher(matcher.ImpactMatcher):

    def __init__(self, parser: spacy.language, lang: str = 'en', impact_model: ImpactModel = None,
                 **kwargs):
        super().__init__(lang=lang, impact_model=impact_model, **kwargs)
        self.parser = parser
        self.lang = lang

    def _iter_text_sentences(self, text: str, doc_id: str = None):
        doc = self.parser(text)
        for si, sent in enumerate(doc.sents):
            self._set_sentence(si, sent, doc_id)
            yield si

    def _set_sentence(self, sentence_index: int, sentence: Union[str, SpacySentence], doc_id: str) -> None:
        self._reset_sentence()
        if isinstance(sentence, str):
            sentence = self.parser(sentence)
        self.sentence_string = sentence.text
        self.sentence_index = sentence_index
        self.doc_id = doc_id
        for si, spacy_token in enumerate(sentence):
            token = Token(
                word=spacy_token.text,
                index=si,
                lemma=spacy_token.lemma_,
                pos=spacy_token.pos_.lower()
            )
            self._add_sentence_token(token)
            if not spacy_token.is_stop:
                self.add_candidate_rules(spacy_token.text, spacy_token.lemma_)
