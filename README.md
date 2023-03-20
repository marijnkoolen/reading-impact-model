# reading-impact-model
Reading Impact Model for analyzing reading impact in online book reviews.

## Usage

Basic usage of the Dutch and English language impact models:

```python
from reading_impact_model.matcher import Matcher
from reading_impact_model import model_loader

impact_model_nl = model_loader(lang='nl')
matcher_nl = Matcher(impact_model_nl, debug=False)

sent_nl = 'Dit boek is meeslepend.'

matches = matcher_nl.match_rules(sentence=sent_nl)

for match in matches:
    print(match.match_word)  # 'meeslepend'
    print(match.impact_term)  # 'meeslepend'
    print(match.impact_term_type)  # 'Affect'
    for condition_match in match.condition_matches:
        print(condition_match.match_word)  # 'boek'
        print(condition_match.condition_term)  # 'boek'
        print(condition_match.condition_type)  # 'general'

impact_model_en = model_loader(lang='en')
matcher_en = Matcher(impact_model_en, debug=False)

sent_en = 'The theme is beautifully addressed by the author with witty banter.'

matches = matcher_en.match_rules(sentence=sent_en)
for match in matches:
    print(match.json)

```


The matcher accepts sentences as string but also Spacy sent objects:

```python
import spacy
from reading_impact_model.matcher import Matcher
from reading_impact_model import model_loader

impact_model_nl = model_loader(lang='nl')
matcher_nl = Matcher(impact_model_nl, debug=False)

nlp = spacy.load('nl_core_news_lg')

sentence = 'Ik werd echt helemaal meegesleept door het verhaal, want het was erg meeslepend zodat ik me liet meeslepen.'

doc = nlp(sentence)
for sent in doc.sents:
    print(sent)
    matches = matcher_nl.match_rules(sentence=sent)
    print('matches:', matches)
```
