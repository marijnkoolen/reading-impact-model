# reading-impact-model
Reading Impact Model for analyzing reading impact in online book reviews.

- [Explanation of the impact types](./docs/impact.md)
- [Examples of impact types](./docs/examples.md)
- [Installation and Usage](#installation-and-usage)
- [Citing](#citing)
- [Contributors](#contributors)

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

## Installation and Usage

You can install the package via pip:

```
pip install reading-impact-model
```

Basic usage of the English language impact model:

```python
from reading_impact_model.matchers.matcher import ImpactMatcher

matcher = ImpactMatcher(lang='en')

matcher.analyse_text('The book has beautiful writing.', doc_id='some_doc_id')
```

Which gives the following output:

```python
[{'doc_id': 'some_doc_id',
  'sentence_index': None,
  'sentence': 'The book has beautiful writing.',
  'reflection': 0,
  'style': 1,
  'attention': 0,
  'humor': 0,
  'surprise': 0,
  'narrative': 0,
  'negative': 0,
  'positive': 1,
  'match_index': 3,
  'impact_term_type': 'term',
  'impact_term': 'beautiful',
  'impact_type': 'Style',
  'match_lemma': 'beautiful',
  'match_word': 'beautiful',
  'condition_match_index': 4,
  'condition_term': 'writing',
  'condition_match_lemma': 'writing',
  'condition_type': 'style',
  'condition_match_word': 'writing'}]
```


There are different matchers that can incorporate syntax parsers to 
add POS and lemma information to word tokens, for improved rule matching.

E.g. the `SpacyMatcher` accepts a Spacy parser (and requires you to have 
installed spacy and an appropriate language model.)
```python
from reading_impact_model.matchers.spacy_matcher import SpacyMatcher
import spacy

nlp = spacy.load('en_core_web_trf') 
matcher = SpacyMatcher(parser=nlp)
```

Which matches the lemma _sentence_ instead of the word _sentences_, which is not in the aspect dictionary.

```python
[{'doc_id': 'some_doc_id',
  'sentence_index': 0,
  'sentence': 'The book contains some beautifully written sentences.',
  'style': 1,
  'surprise': 0,
  'negative': 0,
  'narrative': 0,
  'humor': 0,
  'attention': 0,
  'reflection': 0,
  'positive': 1,
  'match_index': 4,
  'impact_type': 'Style',
  'impact_term': 'beautifully',
  'match_word': 'beautifully',
  'impact_term_type': 'term',
  'match_lemma': 'beautifully',
  'condition_type': 'style',
  'condition_match_word': 'sentences',
  'condition_match_index': 6,
  'condition_match_lemma': 'sentence',
  'condition_term': 'sentence'}]
```

## Citing

If you use this package, please cite the following publications:

- Boot, P., & Koolen, M. (2020). [Captivating, splendid or instructive? 
Assessing the impact of reading in online book reviews.](https://www.jbe-platform.com/content/journals/10.1075/ssol.20003.boo) 
Scientific Study of Literature, 10(1), 35-63. ([pre-pub PDF](https://marijnkoolen.com/publications/2020/boot2020captivating.pdf))
- Koolen, M., Neugarten, J., & Boot, P. (2022). [‘This book makes me 
happy and sad and I love it’. A Rule-based Model for Extracting Reading 
Impact from English Book Reviews.](https://jcls.io/article/id/104/)
Journal of Computational Literary Studies, 1(1).

## Contributors

The `reading-impact-model` package was developed by Marijn Koolen. The rule
set and dictionaries were created by Peter Boot, Julia Neugarten and Marijn
Koolen.

The following people are or have been involved in the Impact & Fiction project:

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
