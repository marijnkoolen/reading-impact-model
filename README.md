# reading-impact-model
Reading Impact Model for analyzing reading impact in online book reviews.

## Usage

Basic usage of the English language impact model:
```python
from reading_impact_model.matcher import Matcher
from reading_impact_model import model_loader

impact_model_en = model_loader(lang='en')
matcher_en = Matcher(impact_model_en, debug=False)

sent_en = 'The writing is beautiful.'

matches = matcher_en.match_rules(sentence=sent_en)

for match in matches:
    print(match.match_word)                  # 'beautiful'
    print(match.impact_term)                 # 'beautiful'
    print(match.impact_term_type)            # 'style'
    for condition_match in match.condition_matches:
        print(condition_match.match_word)     # 'writing'
        print(condition_match.condition_term) # 'writing'
        print(condition_match.condition_type) # 'style'

```


The matcher accepts sentences as string but also Spacy sent objects:

```python
import spacy
from reading_impact_model.matcher import Matcher
from reading_impact_model import model_loader

impact_model = model_loader(lang='en')
matcher = Matcher(impact_model, debug=False)

nlp = spacy.load('en_core_news_lg')

sentence = 'The dialogue is full of witty banter.'

doc = nlp(sentence)
for sent in doc.sents:
    print(sent)
    matches = matcher.match_rules(sentence=sent)
    for match in matches:
        print(match.json)
```
