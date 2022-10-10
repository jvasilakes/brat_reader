`pybrat` is a simple package for reading brat-formatted text annotations (https://brat.nlplab.org/).

<https://pybrat.readthedocs.io/>

# Installation
`pybrat` is written for Python 3 and has no external dependencies. Install it with

```
python setup.py develop
```

Using `develop` should update your installed version when you pull changes from the github.


## Uninstallation

```
python setup.py develop --uninstall
```

# Usage

The `pybrat.BratAnnotations` class automatically links events to their associated text spans and attributes.
Parse a `.ann` file and iterate through the contents with

```python
>>> from pybrat import BratAnnotations
>>> anns = BratAnnotations.from_file("/path/to/file.ann")
>>> for ann in anns:
>>> 	  print(ann)
... "E1	PROCESS_OF:T8 PathologicFunction:T5 AgeGroup:T6
```

By default the `__iter__` method will iterate through the highest level annotations.
You can iterate through specific types of annotations with the `.spans`, `.attributes`, and `.events` properties. E.g.

```python
>>> for span in anns.spans:
>>>     print(span)
... "T8	PROCESS_OF 86 88	in"
```

You can output brat formatted annotations simply by calling `str(ann)` or `print(ann)`. This works for individual annotations,
as shown above, or for a `BratAnnotations` instance.

```python
>>> anns = BratAnnotations.from_file("/path/to/file.ann")
>>> print(anns)
... """
T6	AgeGroup 89 97	children
T5	PathologicFunction 73 79	reflux
T8	PROCESS_OF 86 88	in
E1	PROCESS_OF:T8 PathologicFunction:T5 AgeGroup:T6
...
"""
```

New! You can specify either raw text or sentence-segmented JSONL format text.
This allows you to easily cross-reference annotations with their associated text spans.

JSONL formatted sentences
```
$> cat sentences.jsonl

{"sent_index": 1,
 "start_char": 0,
 "end_char: 23,
 "_text": "The cat sat on the mat."}
```

```python
>>> from pybrat import BratAnnotations, BratText
>>> anns = BratAnnotations.from_file("path/to/file.ann")
>>> anntxt = BratText.from_files(text="path/to/file.txt", sentences="path/to/file.jsonl")
>>> print(anns.events[0])
... "E1	SIT:T2 Animal:T1 Location:T3
>>> event_sentences = annstxt.sentences(anns.events[0])
>>> print(event_sentences)
... [{"sent_index": 1,
...   "start_char": 0,
...   "end_char": 23,
...   "_text": "The cat sat on the mat."}]
```
