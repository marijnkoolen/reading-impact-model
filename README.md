# reading-impact-model
Reading Impact Model for analyzing reading impact in online book reviews.

## Usage

Basic usage of the Dutch and English language impact models:
```python
from matcher import Matcher
from impact_model import model_loader

impact_model_nl = model_loader(lang='nl')
matcher_nl = Matcher(impact_model, debug=False)

sent_nl = 'Dit boek is meeslepend.'

matches = matcher_nl.match_rules(sentence=sent)

for match in matches:
    print(match.match_word)                  # 'meeslepend'
    print(match.impact_term)                 # 'meeslepend'
    print(match.impact_term_type)            # 'Affect'
    print(match.aspect_match.match_word)     # 'boek'
    print(match.aspect_match.condition_term) # 'boek'
    print(match.aspect_match.condition_type) # 'general'

impact_model_en = model_loader(lang='en')
matcher_en = Matcher(impact_model, debug=False)

sent_en = 'This book is disappointing.'

matches = matcher_en.match_rules(sentence=sent)

```


The matcher accepts sentences as string but also Spacy sent objects:
```python
import spacy

nlp = spacy.load('nl_core_news_lg')

sentence = 'Ik werd echt helemaal meegesleept door het verhaal, want het was erg meeslepend zodat ik me liet meeslepen.'

doc = nlp(sentence)
for sent in doc.sents:
    print(sent)
    matches = matcher.match_rules(sentence=sent)
    print('matches:', matches)
```
