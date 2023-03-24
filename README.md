# reading-impact-model
Reading Impact Model for analyzing reading impact in online book reviews.

- [Impact categories](./docs/impact.md)
- [Examples](./docs/examples.md)
- [Usage](#usage)

## The Impact of Fiction

How does your favorite book make you feel?

If you’re an avid reader, this question might be hard to answer. Books can make
us feel extatically happy or deeply sad. Books can inspire us, motivate us, or
make us feel like we are a part of something that matters. As long as stories
have existed, they have made people laugh, and they have made people cry.

In this research project, we are trying to measure the emotional impact of books
and stories, by analyzing the kind of emotional responses that readers express in
online reviews.

The <a href="https://impactandfiction.huygens.knaw.nl">Impact of Fiction</a> is a 
project of the <a href="https://huygens.knaw.nl">Huygens Institute</a> and the
<a href="https://huc.knaw.nl">KNAW Humanities Cluster</a>,
coordinated by Peter Boot (Huygens) and Marijn Koolen (KNAW Humanities Cluster).

## Computational Analysis of Reading Impact

There are millions upon millions of reviews on the internet today. Because of the
staggering number of online reviews available, computational analysis is the ideal
tool for analyzing them. But emotional impact is not easy to detect computationally.
That’s why we’ve created a list of words relating to features from literature
(aspect-terms) and a list of words relating to literature’s emotional impact
(impact-terms) and a set of rules formulated to measure impact in relation to
specific aspects.

Here’s an example:

<table class="rule-example">
    <tbody>
        <tr>
            <td>lovely</td>
            <td>+</td>
            <td>character</td>
            <td>=</td>
            <td>narrative engagement</td>
        </tr>
        <tr>
            <td>[impact-term]</td>
            <td>+</td>
            <td>[aspect-term]</td>
            <td>=</td>
            <td>type of impact</td>
        </tr>
    </tbody>
</table>

By looking at examples from a large set of online reviews, we formulated more than
1300 rules of this kind, measuring different types of impact. For an explanation of
our categories of impact, go to the “Explanation of impact” page.

Here’s another example: In 2020, researchers at the Huygens Institute completed a similar
research project on <a href="https://www.jbe-platform.com/content/journals/10.1075/ssol.20003.boo">Dutch online reviews.</a>
They found, among other things, that
Harry Potter and the Half-Blood Prince scored exceptionally high on use of the
word “magisch” (magical). Any human who knows Harry Potter could guess that this
doesn’t mean an exceptionally high number of reviewers had a magical reading
experience. Rather, in reference to Harry Potter, the word “magical” has little
to do with emotional response because the plot is actually about magic. 

There are lots of other fun and interesting things you could do if you had a clear
sense of the emotional impact of books. For example, this previous study into
Dutch reviews suggested that appreciation of a novel’s style is linked to reflection
on that novel. On the other hand, narrative engagement and mentions of style or
reflection are negatively correlated, meaning that books that are have a very
engaging, often suspenseful narrative are less frequently described as having an
affecting style or inviting reflection. Think of your favorite thriller: is this
true in that case?

## Usage

Basic usage of the English language impact model:

```python
from reading_impact_model.matchers.matcher import Matcher
from reading_impact_model import model_loader

impact_model_en = model_loader(lang='en')
matcher_en = Matcher(impact_model_en, debug=False)

sent_en = 'The writing is beautiful.'

matches = matcher_en.match_rules(sentence=sent_en)

for match in matches:
    print(match.match_word)  # 'beautiful'
    print(match.impact_term)  # 'beautiful'
    print(match.impact_term_type)  # 'style'
    for condition_match in match.condition_matches:
        print(condition_match.match_word)  # 'writing'
        print(condition_match.condition_term)  # 'writing'
        print(condition_match.condition_type)  # 'style'

```


The matcher accepts sentences as string but also Spacy sent objects:

```python
import spacy
from reading_impact_model.matchers.matcher import Matcher
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

<h3>Contributors</h3>

The following people have been involved in this project:

<ul>
    <li>Peter Boot</li>
    <li>Marijn Koolen</li>
    <li>Joris van Zundert</li>
    <li>Julia Neugarten</li>
    <li>Olivia Fialho</li>
    <li>Willem van Hage</li>
    <li>Ole Mussmann</li>
    <li>Carsten Schnober</li>
</ul>
