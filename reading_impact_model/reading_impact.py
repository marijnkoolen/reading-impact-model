from impact_model import ImpactModel
from reading_impact_model.matchers.alpino_matcher import AlpinoSentence, AlpinoError


class ReadingImpact:

    def __init__(self, impact_model: ImpactModel):
        if not impact_model or not isinstance(impact_model, ImpactModel):
            raise TypeError("Matcher must be instantiated with an ImpactModel object")
        self.impact_model = impact_model
        self.model = None
        self.sentence = None
        self.sentence_type = None

    def set_sentence(self, sentence):
        if isinstance(sentence, AlpinoSentence):
            self.sentence_type = 'alpino'
            self.sentence = sentence
        elif isinstance(sentence, object):
            self.sentence = AlpinoSentence(sentence)
        else:
            raise AlpinoError(
                "sentence must be an AlpinoSentence object or a JSON representation of Alpino XML output")
