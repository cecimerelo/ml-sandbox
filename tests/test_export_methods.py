"""The exported method table.

The export exists so the application need not keep its own copy (D-024). A stale export
would defeat that silently — the tool would offer methods the study no longer evaluates,
or omit ones it does.
"""

import json

from mlsandbox.config import PROJECT_ROOT
from mlsandbox.methods import METHODS
from scripts.export_methods import EXPORT_PATH, FIELD_DOCS, build


def exported() -> dict:
    return json.loads(EXPORT_PATH.read_text(encoding="utf-8"))


def test_the_committed_export_matches_the_registry():
    # Fails when the registry changes and the export is not regenerated, which is the whole
    # failure mode the export was introduced to prevent.
    assert exported()["methods"] == build()["methods"]


def test_the_export_covers_every_registered_method():
    assert {m["name"] for m in exported()["methods"]} == set(METHODS)


def test_every_exported_field_is_documented():
    # Someone will open this file without the conversation that produced it, and JSON has
    # no comments.
    fields = {key for method in exported()["methods"] for key in method}
    assert fields <= set(FIELD_DOCS), sorted(fields - set(FIELD_DOCS))


def test_incompatibility_is_present_exactly_where_a_method_does_not_apply():
    for method in exported()["methods"]:
        unsupported = {"classification", "regression"} - set(method["tasks"])
        assert set(method["incompatibility"]) == unsupported, method["name"]


def test_incompatibility_reasons_are_sentences_not_codes():
    # FR-8.3 shows these to a user with no ML background, so they have to be readable.
    for method in exported()["methods"]:
        for reason in method["incompatibility"].values():
            assert reason.endswith("."), method["name"]
            assert " " in reason.strip(), method["name"]


def test_the_export_lives_where_the_application_can_read_it():
    assert EXPORT_PATH.parent == PROJECT_ROOT / "config"
