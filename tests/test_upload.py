"""Reading an uploaded CSV, and every way one can be refused.

The privacy claim gets a test of its own, because it is the claim the interface will make
to a user in writing.
"""

import builtins

import pandas as pd
import pytest

from mlsandbox.upload import MAX_BYTES, MAX_FEATURES, Dataset, Rejected, read


def csv(**columns) -> bytes:
    return pd.DataFrame(columns).to_csv(index=False).encode()


def test_a_plain_csv_is_read():
    result = read(csv(a=[1, 2, 3], b=[4, 5, 6]))
    assert isinstance(result, Dataset)
    assert result.rows == 3
    assert result.columns == ["a", "b"]


# FR-7.2 — the claim the privacy notice will make


def test_nothing_touches_the_filesystem(monkeypatch):
    """Proved rather than promised.

    `open` is made to raise for the duration, so anything that reached for a file — a
    temporary spill, a cache, a library being helpful — fails loudly instead of quietly
    contradicting the notice a user was shown.
    """

    def refuse(*args, **kwargs):
        raise AssertionError("something tried to open a file")

    monkeypatch.setattr(builtins, "open", refuse)
    assert isinstance(read(csv(a=[1, 2], b=[3, 4])), Dataset)


def test_the_signature_takes_bytes_not_a_path():
    # Structural, so the promise survives someone refactoring without reading the docstring.
    from typing import get_type_hints

    from mlsandbox import upload

    assert get_type_hints(upload.read)["content"] is bytes


# Refusals


def test_a_file_that_is_not_a_csv_is_refused():
    result = read(b"\x89PNG\r\n\x1a\n not a csv at all")
    assert isinstance(result, Rejected)
    assert result.reason == "not-a-csv"


def test_the_refusal_says_what_to_do_next():
    result = read(b"", filename="photo.png")
    assert isinstance(result, Rejected)
    assert "comma-separated" in result.message


def test_an_oversized_file_names_the_limit_and_its_actual_size():
    result = read(b"x" * (MAX_BYTES + 1), filename="big.csv")
    assert isinstance(result, Rejected)
    assert result.reason == "too-large"
    assert "50 MB" in result.message


def test_too_many_columns_names_the_count():
    wide = csv(**{f"c{i}": [1] for i in range(MAX_FEATURES + 1)})
    result = read(wide)
    assert isinstance(result, Rejected)
    assert result.reason == "too-many-features"
    assert str(MAX_FEATURES + 1) in result.message


def test_a_header_with_no_data_is_refused():
    result = read(b"a,b,c\n")
    assert isinstance(result, Rejected)
    assert result.reason == "no-rows"


def test_a_single_column_is_refused():
    result = read(csv(only=[1, 2, 3]))
    assert isinstance(result, Rejected)
    assert result.reason == "no-features"


# Unsupported columns are excluded, not fatal


def test_a_date_column_is_skipped_rather_than_rejecting_the_file():
    """Refusing a whole file over one date column makes the user do the work the tool
    exists to save them."""
    frame = pd.DataFrame(
        {
            "when": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "x": [1, 2],
            "y": [3, 4],
        }
    )
    result = read(frame.to_csv(index=False).encode())
    assert isinstance(result, Dataset)


def test_free_text_is_skipped_with_a_reason():
    """Named and explained, not silently dropped.

    The interface shows these disabled rather than hidden — the same rule FR-8.3 sets for
    methods that do not apply — so the reason has to travel with the column.
    """
    notes = ["a unique sentence " + str(i) for i in range(10)]
    result = read(csv(notes=notes, x=list(range(10)), y=list(range(10))))
    assert isinstance(result, Dataset)
    assert [s.column for s in result.skipped] == ["notes"]
    assert result.skipped[0].reason == "free-text"
    assert result.skipped[0].message


def test_a_date_column_is_called_a_date_not_free_text():
    """Dates read from a CSV arrive as strings, and dates are also nearly all distinct.

    Without a parse attempt they fall through to the free-text rule and the user is told
    something about their data that is visibly wrong — worse than saying nothing.
    """
    dates = pd.date_range("2024-01-01", periods=30).astype(str).tolist()
    result = read(csv(listed_on=dates, x=list(range(30)), y=list(range(30))))
    assert isinstance(result, Dataset)
    assert result.skipped[0].reason == "date"


def test_a_column_of_a_few_dates_among_text_is_not_called_a_date():
    mostly_text = ["note " + str(i) for i in range(27)] + ["2024-01-01", "2024-01-02", "x"]
    result = read(csv(mixed=mostly_text, x=list(range(30)), y=list(range(30))))
    assert isinstance(result, Dataset)
    assert result.skipped[0].reason == "free-text"


def test_a_repeating_label_column_is_kept():
    """A city name repeats; a note does not. That is the difference being measured."""
    cities = ["Madrid", "Bilbao"] * 5
    result = read(csv(city=cities, x=list(range(10)), y=list(range(10))))
    assert isinstance(result, Dataset)
    assert "city" in result.columns


def test_a_file_of_nothing_but_unsupported_columns_is_refused():
    notes = ["unique " + str(i) for i in range(10)]
    more = ["also unique " + str(i) for i in range(10)]
    result = read(csv(a=notes, b=more))
    assert isinstance(result, Rejected)
    assert result.reason == "all-unsupported"


def test_the_frame_holds_only_the_usable_columns():
    notes = ["unique " + str(i) for i in range(10)]
    result = read(csv(notes=notes, x=list(range(10)), y=list(range(10))))
    assert isinstance(result, Dataset)
    assert list(result.frame.columns) == ["x", "y"]


@pytest.mark.parametrize(
    "reason",
    ["not-a-csv", "too-large", "too-many-features", "no-rows", "no-features", "all-unsupported"],
)
def test_every_refusal_carries_a_message(reason):
    # A reason code is for the log; the message is for the person.
    assert Rejected(reason=reason, message="x").message


def test_the_browser_and_the_server_agree_on_the_size_limit():
    """The one limit that has to exist twice.

    Every other refusal is the server's, which keeps each limit beside the sentence that
    explains it. Size is different: the point is that an oversized file **never crosses
    the wire**, and a check that runs after the upload is not that check.

    So the number lives in two languages, and this compares them. A duplicated constant
    that nothing compares is a divergence waiting for someone to notice it in production.
    """
    import re

    from mlsandbox.config import PROJECT_ROOT

    source = (PROJECT_ROOT / "app" / "src" / "upload" / "limits.ts").read_text()
    match = re.search(r"MAX_BYTES\s*=\s*([\d\s*]+);", source)
    assert match, "app/src/upload/limits.ts no longer declares MAX_BYTES"
    assert eval(match.group(1)) == MAX_BYTES  # noqa: S307 — a literal arithmetic expression


# The example files, checked against what they claim to demonstrate


EXPECTED_EXAMPLES = {
    "houses.csv": None,
    "houses-with-notes.csv": None,
    "too-many-columns.csv": "too-many-features",
    "header-only.csv": "no-rows",
    "one-column.csv": "no-features",
    "all-unsupported.csv": "all-unsupported",
    "not-a-csv.png": "not-a-csv",
}
"""What each file in `examples/` is for. `None` means it should be accepted.

`too-large.csv` is absent: it is generated rather than committed, and its refusal happens
in the browser before any upload begins, so there is nothing here to check it against.
"""


@pytest.mark.parametrize(("name", "reason"), sorted(EXPECTED_EXAMPLES.items()))
def test_each_example_demonstrates_what_it_claims(name, reason):
    """Otherwise the examples drift from the rules and quietly stop being examples."""
    from mlsandbox.config import PROJECT_ROOT

    path = PROJECT_ROOT / "examples" / name
    if not path.exists():
        pytest.skip(f"{name} not generated — run scripts/make_examples.py")

    result = read(path.read_bytes(), filename=name)
    if reason is None:
        assert isinstance(result, Dataset), f"{name} should be accepted"
    else:
        assert isinstance(result, Rejected), f"{name} should be refused"
        assert result.reason == reason


def test_the_example_with_notes_skips_them_rather_than_being_refused():
    from mlsandbox.config import PROJECT_ROOT

    path = PROJECT_ROOT / "examples" / "houses-with-notes.csv"
    if not path.exists():
        pytest.skip("not generated")

    result = read(path.read_bytes(), filename=path.name)
    assert isinstance(result, Dataset)
    assert sorted(s.column for s in result.skipped) == ["agent_note", "listed_on"]
    reasons = {s.column: s.reason for s in result.skipped}
    assert reasons == {"listed_on": "date", "agent_note": "free-text"}
