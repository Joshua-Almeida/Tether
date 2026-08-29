from app.rag.extract import extract_text, source_id_for, title_for


def test_source_id_slugs_filename():
    assert source_id_for("Attention Is All You Need.pdf") == "attention-is-all-you-need"


def test_extract_plain_text():
    text = extract_text("notes.txt", b"The model uses self-attention.")
    assert "self-attention" in text


def test_extract_rejects_unknown_type():
    try:
        extract_text("slide.pptx", b"not-a-document")
    except ValueError as exc:
        assert "PDF" in str(exc)
    else:
        raise AssertionError("expected ValueError")
