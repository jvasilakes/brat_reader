import os
import pybrat


def test_spans():
    if os.path.isfile("test_files/test_outputs/spans.ann"):
        os.remove("test_files/test_outputs/spans.ann")
    anns = pybrat.BratAnnotations.from_file(
        "test_files/inputs/spans.ann")
    assert len(anns.spans) > 0
    assert len(anns.attributes) == 1
    assert len(anns.events) == 0

    anns.save_brat("test_files/test_outputs/")
    reread_anns = pybrat.BratAnnotations.from_file(
        "test_files/test_outputs/spans.ann")
    assert len(reread_anns.spans) > 0
    assert len(reread_anns.attributes) == 1
    assert len(reread_anns.events) == 0

    gold_anns = pybrat.BratAnnotations.from_file(
        "test_files/gold_outputs/spans.ann")
    assert gold_anns == anns
    assert gold_anns == reread_anns

    gold_str = open("test_files/gold_outputs/spans.ann").read()
    ann_str = open("test_files/test_outputs/spans.ann").read()
    assert gold_str == ann_str


def test_events():
    if os.path.isfile("test_files/test_outputs/events.ann"):
        os.remove("test_files/test_outputs/events.ann")
    anns = pybrat.BratAnnotations.from_file(
        "test_files/inputs/events.ann")
    assert len(anns._raw_spans) > 0
    assert len(anns._raw_attributes) > 0
    assert len(anns._raw_events) > 0
    anns.save_brat("test_files/test_outputs/")

    reread_anns = pybrat.BratAnnotations.from_file(
        "test_files/test_outputs/events.ann")
    assert len(reread_anns._raw_spans) > 0
    assert len(reread_anns._raw_attributes) > 0
    assert len(reread_anns._raw_events) > 0

    gold_anns = pybrat.BratAnnotations.from_file(
        "test_files/gold_outputs/events.ann")
    assert gold_anns == anns
    assert gold_anns == reread_anns

    gold_str = open("test_files/gold_outputs/events.ann").read()
    ann_str = open("test_files/test_outputs/events.ann").read()
    assert gold_str == ann_str


def test_attributes():
    if os.path.isfile("test_files/test_outputs/attributes.ann"):
        os.remove("test_files/test_outputs/attributes.ann")
    anns = pybrat.BratAnnotations.from_file(
        "test_files/inputs/attributes.ann")
    assert len(anns.spans) > 0
    assert len(anns.attributes) > 0
    assert len(anns.events) == 1

    anns.save_brat("test_files/test_outputs/")
    reread_anns = pybrat.BratAnnotations.from_file(
        "test_files/test_outputs/attributes.ann")
    assert len(reread_anns.spans) > 0
    assert len(reread_anns.attributes) > 0
    assert len(reread_anns.events) == 1

    gold_anns = pybrat.BratAnnotations.from_file(
        "test_files/gold_outputs/attributes.ann")
    assert gold_anns == anns
    assert gold_anns == reread_anns

    gold_str = open("test_files/gold_outputs/attributes.ann").read()
    ann_str = open("test_files/test_outputs/attributes.ann").read()
    assert gold_str == ann_str


def test_brat_text():
    anns = pybrat.BratAnnotations.from_file(
        "test_files/text_files/1.ann")
    anntxt = pybrat.BratText.from_files(
        text="test_files/text_files/1.txt",
        sentences="test_files/text_files/1.jsonl")

    for span in anns.spans:
        text_span_idx = anntxt.text(span.start_index, span.end_index)
        assert text_span_idx == span.text
        text_span = anntxt.text(annotations=[span])
        assert text_span == span.text

        tok_span_idx = anntxt.tokens(span.start_index, span.end_index)
        assert span.text in ' '.join(tok_span_idx)
        tok_span = anntxt.tokens(annotations=[span])
        assert span.text in ' '.join(tok_span)

        sent_span_idx = anntxt.sentences(span.start_index, span.end_index)
        assert span.text in ' '.join([s["_text"] for s in sent_span_idx])
        sent_span = anntxt.sentences(annotations=[span])
        assert span.text in ' '.join([s["_text"] for s in sent_span])


if __name__ == "__main__":
    test_spans()
    test_attributes()
    test_events()
    test_brat_text()
    print("PASSED!")
