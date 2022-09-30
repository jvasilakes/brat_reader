import re
import os
import html
from collections import defaultdict
from pathlib import Path


class Annotation(object):
    """
    The base class for brat annotations.
    Use Span, Event, or Attribute instead of this class.
    """
    def __init__(self, _id, _type, _source_file):
        self._id = _id
        self._type = _type
        self._source_file = _source_file
        if _source_file is not None:
            self._source_file = os.path.basename(_source_file)

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    def update(self, key, value):
        self.__dict__[key] = value

    def __eq__(self, other):
        raise NotImplementedError()

    def __hash__(self):
        raise NotImplementedError()

    def __str__(self):
        return self.to_brat_str()

    def __repr__(self):
        field_strings = []
        for (k, v) in self.__dict__.items():
            if k.startswith('_'):
                continue
            if isinstance(v, Annotation):
                v_rep = v.short_repr()
            elif isinstance(v, dict):
                repr_dict = {}
                for (sub_k, sub_v) in v.items():
                    if isinstance(sub_v, Annotation):
                        sub_v_rep = sub_v.short_repr()
                    else:
                        sub_v_rep = repr(sub_v)
                    repr_dict[sub_k] = sub_v_rep
                v_rep = repr(repr_dict)
            elif isinstance(v, (list, tuple)):
                repr_list = []
                for sub_v in v:
                    if isinstance(sub_v, Annotation):
                        sub_v_rep = sub_v.short_repr()
                    else:
                        sub_v_rep = repr(sub_v)
                    repr_list.append(sub_v_rep)
                v_rep = repr(repr_list)
            else:
                v_rep = repr(v)
            field_strings.append(f"{k}: {v_rep}")
        fields_str = ', '.join(field_strings)
        class_name = str(self.__class__).split('.')[-1][:-2]
        rep = f"{class_name}({fields_str})"
        return rep

    def short_repr(self):
        class_name = str(self.__class__).split('.')[-1][:-2]
        contents = [f"id: {self.id})"]
        if "_type" in self.__dict__:
            contents.insert(0, f"type: {self.type}")
        contents_str = ', '.join(contents)
        return f"{class_name}({contents_str})"

    def copy(self):
        return self.__class__(**self.__dict__)

    @staticmethod
    def _resolve_file_path(path):
        try:
            here = Path(path).resolve()
            abspath = str(here.absolute())
        except TypeError:
            abspath = path
        return abspath

    def to_brat_str(self):
        raise NotImplementedError()


class Span(Annotation):
    """
    A brat span. I.e., a span of text.

    :param str _id: the unique numerical identifier of this span with the 'T'
                    prefix. E.g., 'T3'.
    :param int start_index: the starting character index of this span
                            in the associated document.
    :param int end_index: the ending character index of this span
                          in the associated document.
    :param str text: the actual span text
    :param str _type: (Optional) a string giving the type of this span,
                      e.g., for NER. Default is 'Span'.
    :param str _source_file: (Optional), the name of the .ann file which
                             contains this span.
    """
    def __init__(self, _id, start_index, end_index,
                 text, _type="Span", _source_file=None):
        super().__init__(_id=_id, _type=_type, _source_file=_source_file)
        self.start_index = start_index
        self.end_index = end_index
        self.text = text

    def __eq__(self, other):
        if not isinstance(other, Span):
            return False
        return all([
            self.type == other.type,
            self.start_index == other.start_index,
            self.end_index == other.end_index,
            self.text == other.text,
        ])

    def __hash__(self):
        return hash((
            self.type,
            self.start_index,
            self.end_index,
            self.text,
        ))

    def to_brat_str(self, output_references=False):
        """
        Format this Span instance as a brat string.

        :param bool output_references: unused
        """
        # output_references is unused but simplifies to_brat_str for Attribute
        return f"{self.id}\t{self.type} {self.start_index} {self.end_index}\t{self.text}"  # noqa


class Attribute(Annotation):
    """
    A brat attribute. Can be attached to Spans or Events.

    :param str _id: the unique numerical identifier of this attribute with
                    the 'A' prefix. E.g., 'A5'.
    :param Any value: the value of this attribute.
    :param Annotation reference: the corresponding Span or Event instance.
    :param str _type: (Optional) a string giving the type of this attribute.
                      Default is 'Attribute'.
    :param str _source_file: (Optional), the name of the .ann file which
                             contains this span.
    """
    def __init__(self, _id, value, reference,
                 _type="Attribute", _source_file=None):
        super().__init__(_id=_id, _type=_type, _source_file=_source_file)
        self.value = value
        self.reference = reference
        if not isinstance(self.reference, (Span, Event, type(None))):
            raise ValueError(f"Attribute reference must be instance of Span, Event, or None. Got {type(self.reference)}.")  # noqa

    def __eq__(self, other):
        if not isinstance(other, Attribute):
            return False
        return all([
            self.type == other.type,
            self.value == other.value,
            # Attributes and events can point to each
            # other, so we'll use IDs to avoid endless recursion.
            self.reference.id == other.reference.id,
        ])

    def __hash__(self):
        return hash((
            self.type,
            self.value,
            self.reference.id,
        ))

    @property
    def span(self):
        if self.reference is None:
            span = None
        elif isinstance(self.reference, Span):
            span = self.reference
        elif isinstance(self.reference, Event):
            span = self.reference.spans
        else:
            raise ValueError(f"reference must be Span, Event, or None. Got {type(self.reference)}.")  # noqa
        return span

    @property
    def start_index(self):
        """
        The starting character index of this Attribute's reference.
        """
        if self.reference is None:
            idx = None
        elif isinstance(self.reference, (Span, Event)):
            idx = self.reference.start_index
        else:
            raise ValueError(f"reference must be Span, Event, or None. Got {type(self.reference)}.")  # noqa
        return idx

    @property
    def end_index(self):
        """
        The ending character index of this Attribute's reference.
        """
        if self.reference is None:
            idx = None
        elif isinstance(self.reference, (Span, Event)):
            idx = self.reference.end_index
        else:
            raise ValueError(f"reference must be Span, Event, or None. Got {type(self.reference)}.")  # noqa
        return idx

    def to_brat_str(self, output_references=False):
        """
        Format this Attribute instance as a brat string.

        :param bool output_references: If True, also includes the brat string
            of the reference of this Attribute. Default False.
        """
        outlines = []
        if output_references is True:
            if self.reference is not None:
                ref_str = self.reference.to_brat_str(output_references=False)
                outlines.append(ref_str)
        ref_id = self.reference.id
        outlines.append(f"{self.id}\t{self.type} {ref_id} {self.value}")
        return '\n'.join(outlines)


class Event(Annotation):
    """
    A brat event, composed of one or more ordered Span instances.
    brat_reader does not enforce any specific Event structure.

    :param str _id: the unique numerical identifier of this event
                    with the E prefix. E.g., 'E10'.
    :param Span spans: one or more Span instances.
    :param dict attributes: a dictionary of Attribute instances
                            keyed by attribute type.
    :param str _type: (Optional) A type for this Event. Default is 'Event'.
    :param str _source_file: (Optional), the name of the .ann file which
                             contains this span.
    """
    def __init__(self, _id, *spans, attributes=None,
                 _type="Event", _source_file=None):
        super().__init__(_id=_id, _type=_type, _source_file=_source_file)
        for span in spans:
            assert isinstance(span, Span), f"Not a Span instance: {span}"
        self.spans = spans
        self.attributes = attributes or {}
        for attr in self.attributes.values():
            attr.reference = self

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return all([
            self.spans == other.spans,
            self.attributes == other.attributes,
        ])

    @property
    def start_index(self):
        """
        The lowest character index of this Event's spans.
        """
        return min([span.start_index for span in self.spans])

    @property
    def end_index(self):
        """
        The highest character index of this Event's spans.
        """
        return max([span.end_index for span in self.spans])

    def to_brat_str(self, output_references=False):
        """
        Format this Event instance as a brat string.

        :param bool output_references: If True, also includes the brat string
            of the Spans and Attributes of this Event. Default False.
        """
        event_str = f"{self.id}\t"
        for span in self.spans:
            event_str += f"{span.type}:{span.id} "
        outlines = [event_str.strip()]
        if output_references is True:
            attr_strs = [a.to_brat_str(output_references=False)
                         for a in self.attributes.values()]
            outlines.extend(attr_strs)
            for span in self.spans:
                outlines.insert(0, span.to_brat_str())
        brat_str = '\n'.join(outlines)
        return brat_str


class BratAnnotations(object):
    """
    The main class for working with brat annotations.

    You can read annotations from a file.

    .. code-block: python

        import brat_reader as br
        anns = br.BratAnnotations.from_file("path/to/file.ann")

    You can also create a set of annotations from Event instances.

    .. code-block: python

        import brat_reader as br
        event1 = Event("E1", *e1spans)
        event2 = Event("E2", *e2spans)
        anns = br.BratAnnotations.from_events([event1, event2])
    """

    @classmethod
    def from_file(cls, fpath):
        """
        Read brat annotations from the specified file.

        :param str fpath: The path to the ann file.
        :returns: a new BratAnnotations instance.
        """
        spans = []
        events = []
        attributes = []
        with open(fpath, 'r') as inF:
            for line in inF:
                line = line.strip()
                ann_type = line[0]
                if ann_type == 'T':
                    data = parse_brat_span(line)
                    data["_source_file"] = fpath
                    spans.append(data)
                elif ann_type == 'E':
                    data = parse_brat_event(line)
                    data["_source_file"] = fpath
                    events.append(data)
                elif ann_type == 'A':
                    data = parse_brat_attribute(line)
                    data["_source_file"] = fpath
                    attributes.append(data)
                else:
                    raise ValueError(f"Unsupported ann_type '{ann_type}'.")
        annotations = cls(spans=spans, events=events, attributes=attributes)
        return annotations

    @classmethod
    def from_events(cls, events_iter):
        """
        Create a BratAnnotations instance from a collection of Events.

        :param List[Event] events_iter: An iterable over Event instances.
        """
        annotations = cls(spans=[], events=[], attributes=[])
        annotations._events = list(events_iter)
        return annotations

    def __init__(self, spans, events, attributes):
        self._raw_spans = spans
        self._raw_events = events
        self._raw_attributes = attributes
        self._spans = []  # Will hold Span instances
        self._attributes = []  # Will hold Attribute instances
        self._events = []  # Will hold Event instances
        self._resolve()
        self._sorted_spans = None
        self._sorted_attributes = None
        self._sorted_events = None

    def __eq__(self, other):
        if not isinstance(other, BratAnnotations):
            return False
        if len(self.spans) != len(other.spans):
            return False
        for (this_span, other_span) in zip(self.spans, other.spans):
            if this_span != other_span:
                return False
        if len(self.attributes) != len(other.attributes):
            return False
        for (this_attr, other_attr) in zip(self.attributes, other.attributes):
            if this_attr != other_attr:
                return False
        if len(self.events) != len(other.events):
            return False
        for (this_event, other_event) in zip(self.events, other.events):
            if this_event != other_event:
                return False
        return True

    def get_events_by_type(self, event_type):
        return [e for e in self.events if e.type == event_type]

    def get_attributes_by_type(self, attr_type):
        return [a for a in self.attributes if a.type == attr_type]

    def get_spans_by_type(self, span_type):
        return [s for s in self.spans if s.type == span_type]

    @property
    def spans(self):
        if self._sorted_spans is None:
            self._sorted_spans = self._sort_spans_by_index()
        return self._sorted_spans

    @property
    def attributes(self):
        if self._sorted_attributes is None:
            self._sorted_attributes = self._sort_attributes_by_span_index()
        return self._sorted_attributes

    @property
    def events(self):
        if self._sorted_events is None:
            self._sorted_events = self._sort_events_by_span_index()
        return self._sorted_events

    def __iter__(self):
        for ann in self.get_highest_level_annotations():
            yield ann

    def _sort_spans_by_index(self):
        return sorted(self._spans, key=lambda s: s.start_index)

    def _sort_attributes_by_span_index(self):
        # An Attribute may refer to a Span or an Event,
        # so we have to check which is the case. If its an Event,
        # we have to sort by the Event.span
        span_indices = []
        for attr in self._attributes:
            if isinstance(attr.reference, Span):
                span_indices.append(attr.reference.start_index)
            elif isinstance(attr.reference, Event):
                span_indices.append(attr.reference.start_index)
        sorted_indices = sorted(enumerate(span_indices), key=lambda s: s[1])
        sorted_indices = [i for (i, idx) in sorted_indices]
        return [self._attributes[i] for i in sorted_indices]

    def _sort_events_by_span_index(self):
        return sorted(self._events, key=lambda e: e.start_index)

    def _resolve(self):
        """
        Given a set of raw spans, attributes, and events, e.g., as read
        from a .ann file, creates Span, Attribute, and Event instances and
        then links them as specified in the file.
        """
        span_lookup = {}
        attribute_lookup = defaultdict(list)

        for raw_span in self._raw_spans:
            span = Span(**raw_span)
            span_lookup[raw_span["_id"]] = span
            self._spans.append(span)

        for raw_attr in self._raw_attributes:
            ref_id = raw_attr.pop("ref_id")
            ref = span_lookup.get(ref_id, None)
            attribute = Attribute(**raw_attr, reference=ref)
            attribute_lookup[ref_id].append(attribute)
            self._attributes.append(attribute)

        for raw_event in self._raw_events:
            event_spans = []
            for (span_type, span_id) in raw_event["ref_spans"]:
                span = span_lookup[span_id]
                event_spans.append(span)
            event = Event(raw_event["_id"], *event_spans, attributes=None,
                          _source_file=raw_event["_source_file"])
            attrs = attribute_lookup[raw_event["_id"]]
            for attr in attrs:
                attr.reference = event
            attrs_by_type = {attr.type: attr for attr in attrs}
            event.attributes = attrs_by_type
            self._events.append(event)

    def get_highest_level_annotations(self, type=None):
        """
        brat annotations can include only spans, spans + events,
        or spans + events + attributes. This method allows one to
        get the highest-level annotation available in this file.

        In order from highest to lowest level:
          Event
          Attribute
          Span

        :param str type: (Optional) return annotations with the specified type.
        """
        if len(self._events) > 0:
            if type is not None:
                return self.get_events_by_type(type)
            else:
                return self.events
        elif len(self._attributes) > 0:
            if type is not None:
                return self.get_attributes_by_type(type)
            else:
                return self.attributes
        elif len(self._spans) > 0:
            if type is not None:
                return self.get_spans_by_type(type)
            else:
                return self.spans
        else:
            return []

    def __str__(self):
        outlines = []
        for ann in self.get_highest_level_annotations():
            outlines.append(ann.to_brat_str(output_references=True))
        return '\n'.join(outlines)

    def save_brat(self, outdir, filename=None):
        """
        Save these brat annotations to a brat-formatted file.

        :param str outdir: The directory in which to save the file.
        :param str filename: (Optional) The filename to use. If not specified,
                             attempts to use the Annotation._source_file.
        """
        for ann in self.get_highest_level_annotations():
            brat_str = ann.to_brat_str(output_references=True)
            if filename is None and ann._source_file is None:
                raise ValueError("No filename specified.")
            if filename is not None:
                outfile = os.path.join(outdir, filename)
            else:
                bn = os.path.basename(ann._source_file)
                outfile = os.path.join(outdir, bn)
            with open(outfile, 'a') as outF:
                outF.write(brat_str + '\n')

    def get_context(self, ann: Annotation, window=0):
        if self.text is None:
            raise ValueError("No text supplied.")
        if self.text.is_split_into_sentences:
            context = self.text.get_sentences(
                ann.start_index, ann.end_index, window=window)
        else:
            context = self.text.get_tokens(
                ann.start_index, ann.end_index, window=window)
        return context


class BratText(object):
    """
    A simple class for organizing the text that corresponds to a
    file of brat annotations.

    Specify plain text, split sentences, or both.
    >>> bt = BratText(text=plain_text, sentences=list_of_sents)
    >>> bt.text[0:12]  # Plain text at character indices 0 through 12
    >>> bt.tokens(0, 12)  # Tokens spanning character indices 0 through 12
    >>> bt.sentences(0, 12)  # Sentences spanning character indices 0 - 12
    """
    def __init__(self, text=None, sentences=None, tokenizer=None):
        if text is None and sentences is None:
            raise ValueError("Must supply at least one of text or sentences")
        self.is_split_into_sentences = sentences is not None
        if sentences is not None:
            self._sentences_lookup = self._split_sentences(sentences)
        if text is None:
            self.text = self._get_text_from_sentences()
        else:
            self.text = text
        self.tokenizer = self._get_tokenizer(tokenizer)
        self._tokens = None
        self._tokens_lookup = self._tokenize(self.text)

    def sentences(self, start_char=None, end_char=None):
        if self.is_split_into_sentences is False:
            raise ValueError("Text is not split into sentences.")
        if end_char is None:
            if start_char is None:
                end_char = max(list(self._sentences_lookup.keys()))
            else:
                end_char = start_char + 1
        if start_char is None:
            start_char = min(list(self._sentences_lookup.keys()))
        sents = []
        for char_i in range(start_char, end_char):
            try:
                s = self._sentences_lookup[char_i]
            except KeyError:
                continue
            if s not in sents:
                sents.append(s)
        return sents

    def tokens(self, start_char=None, end_char=None):
        if end_char is None:
            if start_char is None:
                end_char = len(self.text)
            else:
                end_char = start_char + 1
        if start_char is None:
            start_char = 0

        tokens = []
        for char_i in range(start_char, end_char):
            try:
                t = self._tokens_lookup[char_i]
            except KeyError:
                continue
            if len(tokens) == 0 or t != tokens[-1]:
                tokens.append(t)
        return tokens

    def _get_text_from_sentences(self):
        text = ''
        for sent in self.sentences():
            text += ' ' * (sent["start_char"] - len(text))
            text += sent["_text"]
        return text

    def _split_sentences(self, sentences):
        assert isinstance(sentences, list)
        is_str = all([isinstance(sent, str) for sent in sentences])
        is_dict = all([isinstance(sent, dict) for sent in sentences])
        assert is_str or is_dict

        sentence_lookup = {}
        if is_str:
            # assume sentences passed in order with no character offsets
            current_start = 0
            for (i, sent) in enumerate(sentences):
                current_end = current_start + len(sent)
                sent_data = {"sent_index": i,
                             "start_char": current_start,
                             "end_char": current_end,
                             "_text": sent}
                for char_idx in range(current_start, current_end):
                    sentence_lookup[char_idx] = sent_data
                current_start = current_end
        elif is_dict:
            seen_indices = set()
            for sent in sentences:
                assert "sent_index" in sent
                assert "start_char" in sent
                assert "end_char" in sent
                assert "_text" in sent
                assert sent["sent_index"] not in seen_indices, "Duplicate sent_index!"  # noqa
                seen_indices.add(sent["sent_index"])
                for char_idx in range(sent["start_char"], sent["end_char"]):
                    sentence_lookup[char_idx] = sent
        return sentence_lookup

    def _get_tokenizer(self, tokenizer):
        if tokenizer is None:
            tokenizer = RegexTokenizer()
        return tokenizer

    def _tokenize(self, text):
        tokens, char_ranges = self.tokenizer(text)
        token_lookup = {}
        for (tok, crange) in zip(tokens, char_ranges):
            for ci in range(*crange):
                token_lookup[ci] = tok
        return token_lookup


class RegexTokenizer(object):
    """
    A very simple tokenizer that splits on whitespace by default.

    .. code-block: python

        import brat_reader as br
        tokenizer = br.RegexTokenizer()
        text = "The cat in the hat"
        tokens, token_char_ranges = tokenizer(text)
    """
    def __init__(self, split_pattern=r'\s'):
        self.split_pattern = re.compile(split_pattern)

    def __call__(self, text: str):
        tokens = []
        token_char_idxs = []
        current_text = ''
        current_char_idxs = []
        for (i, char) in enumerate(text):
            if self.split_pattern.match(char):
                if len(current_text) > 0:
                    tokens.append(current_text)
                    token_char_idxs.append(current_char_idxs)
                current_text = ''
                current_char_idxs = []
            else:
                current_text += char
                current_char_idxs.append(i)
        if len(current_text) > 0:
            tokens.append(current_text)
            token_char_idxs.append(current_char_idxs)
        token_ranges = [(char_idxs[0], char_idxs[-1])
                        for char_idxs in token_char_idxs]
        return tokens, token_ranges


def parse_brat_span(line):
    # Sometimes things like '&quot;' appear
    line = html.unescape(line)
    uid, label, other = line.split(maxsplit=2)
    # start1 end1;start2 end2
    if re.match(r'[0-9]+\s[0-9]+\s?;\s?[0-9]+\s[0-9]+', other):
        # Occasionally, non-contiguous spans occur in the n2c2 2022 data.
        # Merge these to be contiguous.
        text = ''
        spans = other.split(';', maxsplit=1)
        start_idx = None
        for span in spans:
            start_idx_tmp, end_idx_plus = span.split(maxsplit=1)
            if start_idx is None:
                start_idx = start_idx_tmp
            end_idx_split = end_idx_plus.split(maxsplit=1)
            if len(end_idx_split) > 1:
                end_idx, text = end_idx_split
            else:
                end_idx = end_idx_split[0]
    # start end
    else:
        start_idx, end_idx, text = other.split(maxsplit=2)

    return {"_id": uid,
            "_type": label,
            "start_index": int(start_idx),
            "end_index": int(end_idx),
            "text": text}


def parse_brat_event(line):
    fields = line.split()
    assert len(fields) >= 2
    uid = fields[0]
    spans = fields[1:]
    ref_spans = []
    for span in spans:
        label, ref = span.split(':')
        ref_spans.append((label, ref))
    return {"_id": uid,
            "_type": label,
            "ref_spans": ref_spans}


def parse_brat_attribute(line):
    fields = line.split()
    if fields[1] == "Negation":
        if len(fields) == 3:
            fields.append("Negated")
    assert len(fields) == 4
    uid, label, ref, value = fields
    return {"_id": uid,
            "_type": label,
            "value": value,
            "ref_id": ref}
