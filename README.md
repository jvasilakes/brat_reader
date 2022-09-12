`brat_reader` is a simple package for reading brat-formatted text annotations (https://brat.nlplab.org/).

# Installation
`brat_reader` has no external dependencies. Install it with

```
python setup.py develop
```

Using `develop` should update your installed version when you pull changes from the github.

## Uninstallation

```
python setup.py develop --uninstall
```

# Usage

The `brat_reader.BratAnnotations` class automatically links events to their associated text spans and attributes.
Parse a `.ann` file and iterate through the contents with

```python
>>> from brat_reader import BratAnnotations
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


`Span`, `Attribute`, and `Event` instances have the following properties.

## `Span`
* `id : str`
* `start_index : int`
* `end_index : int`
* `text : str`

## `Attribute`
* `id : str`
* `type : str`
* `value : {str,int}`

## `Event`
* `id : str`
* `spans : list(Span)`
* `attributes : dict({str: Attribute})`
