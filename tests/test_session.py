"""What a session records — and the ways a metric can be fabricated by the interface.

The product is the instrument. These tests exist because the failures here do not look
like failures: they look like encouraging numbers.
"""

import pytest

from mlsandbox.session import (
    DeliberateSelection,
    SessionRecord,
    SessionStore,
    TrainedMethod,
    new_record,
)

DRIVERS = {"task": "binary classification", "rows": "500-10k"}


def record(**overrides) -> SessionRecord:
    defaults = dict(session="s1", drivers=DRIVERS, recommended="random_forest")
    return new_record(**{**defaults, **overrides})


# Origin — the distinction the whole record exists for


def test_auto_training_is_never_a_choice():
    """FR-8.4 trains the recommended method every time, by construction.

    Counting that as the user choosing it makes any acceptance metric read 100% every
    session and measure nothing. This was once filed as "not a gap"; it is the gap.
    """
    trained = TrainedMethod(method="random_forest", origin="system")
    assert not trained.is_deliberate


def test_the_recommended_method_is_not_deliberate_just_for_being_in_the_batch():
    session = record(
        trained=[
            TrainedMethod(method="random_forest", origin="system"),
            TrainedMethod(method="knn", origin="system"),
        ]
    )
    assert session.deliberate_methods == []


def test_a_toggled_chip_is_a_choice():
    assert TrainedMethod(method="knn", origin="user").is_deliberate


def test_a_retry_inherits_rather_than_becoming_a_choice():
    """A user rescuing a run that timed out has not decided anything new."""
    assert not TrainedMethod(method="svm_rbf", origin="retry").is_deliberate


# The two acceptance arms, which must never become one number


def test_arm_a_needs_the_user_to_name_the_method():
    session = record(would_use="random_forest")
    assert session.accepted_explicitly


def test_arm_a_is_not_satisfied_by_silence():
    """Someone who answered nothing has not accepted anything.

    Folding silence into the strong arm is the single easiest way to inflate this number,
    and it would not look wrong in the output.
    """
    assert not record().accepted_explicitly


def test_arm_b_counts_silence_but_is_reported_separately():
    session = record()
    assert session.accepted_without_override
    assert not session.accepted_explicitly


def test_arm_b_fails_once_another_method_is_chosen():
    session = record(selections=[DeliberateSelection(method="knn", selector="promoted")])
    assert not session.accepted_without_override


def test_choosing_the_recommendation_itself_satisfies_both():
    session = record(
        would_use="random_forest",
        selections=[DeliberateSelection(method="random_forest", selector="expander")],
    )
    assert session.accepted_explicitly
    assert session.accepted_without_override


def test_the_two_arms_are_separate_properties():
    """Not a single field with a threshold.

    Absence of an override and an explicit pick are different evidence, and the thesis has
    to report them apart. One field would let them be merged by whoever writes the query.
    """
    assert "accepted_explicitly" in dir(SessionRecord)
    assert "accepted_without_override" in dir(SessionRecord)


def test_an_unanswered_prompt_is_a_state_not_a_missing_value():
    # The control is never pre-filled, so `None` is what an untouched one means.
    assert record().would_use is None


# The selector funnel


def test_where_a_method_was_picked_from_is_kept():
    """Three methods are one click away and the rest are behind an accordion.

    Without this, a method's popularity cannot be told apart from its position.
    """
    session = record(selections=[DeliberateSelection(method="knn", selector="expander")])
    assert session.selections[0].selector == "expander"


def test_the_promoted_set_is_recorded():
    session = record(promoted=["random_forest", "boosting", "knn"])
    assert len(session.promoted) == 3


def test_diversity_counts_only_what_was_chosen():
    session = record(
        trained=[TrainedMethod(method=m, origin="system") for m in ("a", "b", "c")],
        selections=[DeliberateSelection(method="knn", selector="promoted")],
    )
    assert session.deliberate_methods == ["knn"]


# Privacy


def test_interactions_are_stored_as_a_count():
    """Never the column names, in any form.

    A hash of `patient_id` is still a stable identifier for `patient_id`, so hashing would
    let the privacy notice keep its wording in a costume (D-035).
    """
    session = record(named_interactions=2)
    assert session.named_interactions == 2
    assert "names" not in session.model_dump()


def test_the_record_carries_bands_rather_than_values():
    session = record()
    assert session.drivers["rows"] == "500-10k"


def test_the_record_has_no_field_that_could_hold_a_column_name():
    # Checked structurally rather than by inspection: a field added later that could carry
    # one should fail here rather than be noticed in a database.
    allowed = {
        "session", "created", "drivers", "named_interactions", "recommended",
        "promoted", "trained", "selections", "would_use",
    }
    assert set(SessionRecord.model_fields) == allowed


# Storage


def test_a_saved_session_round_trips(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    session = record(would_use="knn")
    store.save(session)
    assert store.load("s1") == session


def test_saving_twice_keeps_one_session(tmp_path):
    """A session is edited as it goes — trained, then compared, then answered.

    Appending each state would make the analysis count one session several times.
    """
    store = SessionStore(tmp_path / "sessions.db")
    store.save(record())
    store.save(record(would_use="knn"))
    assert len(store.all()) == 1
    loaded = store.load("s1")
    assert loaded is not None
    assert loaded.would_use == "knn"


def test_an_unknown_session_is_none(tmp_path):
    assert SessionStore(tmp_path / "sessions.db").load("nope") is None


def test_the_store_creates_its_directory(tmp_path):
    SessionStore(tmp_path / "nested" / "sessions.db")
    assert (tmp_path / "nested").exists()


def test_extra_fields_are_refused(tmp_path):
    with pytest.raises(ValueError):
        SessionRecord(
            session="s", created="now", drivers={}, recommended="knn", dataset_name="secret"
        )


# What the thesis reports


def test_the_two_arms_are_reported_as_separate_numbers():
    """Never one "acceptance rate".

    They measure different things, and a single figure would be the weaker of the two
    wearing the name of the stronger.
    """
    from mlsandbox.session import summarise

    records = [
        record(session="a", would_use="random_forest"),
        record(session="b"),
        record(session="c", selections=[DeliberateSelection(method="knn", selector="promoted")]),
    ]
    result = summarise(records)
    assert result.explicit == pytest.approx(1 / 3)
    assert result.without_override == pytest.approx(2 / 3)
    assert result.explicit != result.without_override


def test_the_summary_says_how_much_rests_on_silence():
    """Arm B counts sessions that never answered, so the count of answers is what tells a
    reader how much of it is agreement and how much is absence."""
    from mlsandbox.session import summarise

    result = summarise([record(session="a"), record(session="b", would_use="knn")])
    assert result.answered == 1
    assert result.sessions == 2


def test_diversity_ignores_what_was_trained_automatically():
    from mlsandbox.session import summarise

    records = [
        record(session="a", trained=[TrainedMethod(method="mlp", origin="system")]),
        record(session="b", selections=[DeliberateSelection(method="knn", selector="promoted")]),
    ]
    assert summarise(records).diversity == 1


def test_an_empty_study_reports_zero_rather_than_dividing():
    from mlsandbox.session import summarise

    assert summarise([]).sessions == 0


def test_the_store_has_a_configured_home(tmp_path):
    """Not a path each caller invents.

    A second caller computing it its own way is how the benchmark came to announce there
    were no results while fourteen thousand rows sat on disk.
    """
    from mlsandbox.config import load_config
    from mlsandbox.session import store_for

    assert store_for(load_config()).path == load_config().paths.sessions


def test_session_records_live_outside_the_study_artifacts():
    """Different kind of data, different rules.

    The datasets and results are study artifacts — reproducible, and safe to hand to
    anyone checking the work. This is a record of what people did, and it is neither. It
    must not sit where something sweeping the study's outputs would pick it up.
    """
    from mlsandbox.config import load_config

    paths = load_config().paths
    assert paths.sessions.parent != paths.datasets
    assert not paths.sessions.is_relative_to(paths.datasets)
