from stanza import Pipeline
from stanza.models.common.doc import Sentence as StanzaSentence

from reading_impact_model.matchers import matcher
from reading_impact_model.impact_model import ImpactModel


class StanzaMatcher(matcher.ImpactMatcher):

    def __init__(self, parser: Pipeline, lang: str = 'en', impact_model: ImpactModel = None,
                 **kwargs):
        super().__init__(lang=lang, impact_model=impact_model, **kwargs)
        self.parser = parser
        self.lang = lang

    def _iter_text_sentences(self, text: str):
        doc = self.parser(text)
        for si, sent in enumerate(doc.sentences):
            self._set_sentence(sent)
            yield si

    def _set_sentence(self, sentence: StanzaSentence) -> None:
        self._reset_sentence()
        self.sentence_string = sentence.text
        for stanza_token in sentence.tokens:
            token = {
                'word': stanza_token.to_dict()['text'],
                'lemma': stanza_token.to_dict()['lemma'],
                'pos': stanza_token.to_dict()['upos'].lower()
            }
            self.sentence_tokens.append(token)
            if token['pos'] != 'punct':
                self.add_candidate_rules(token['text'], token['lemma'])
