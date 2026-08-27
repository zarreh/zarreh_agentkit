from pydantic import BaseModel

from zarreh_agentkit.guardrails.projection import project_fields


class Encounter(BaseModel):
    encounter_id: str
    patient_id: str
    start: str
    description: str


def test_project_fields_keeps_only_allowlisted_keys() -> None:
    record = Encounter(
        encounter_id="e1", patient_id="p1", start="2026-01-01", description="Checkup"
    )
    projected = project_fields(record, frozenset({"start", "description"}))
    assert projected == {"start": "2026-01-01", "description": "Checkup"}


def test_project_fields_empty_allowlist_drops_everything() -> None:
    record = Encounter(encounter_id="e1", patient_id="p1", start="2026-01-01", description="x")
    assert project_fields(record, frozenset()) == {}


def test_project_fields_unknown_allowlisted_key_is_ignored() -> None:
    record = Encounter(encounter_id="e1", patient_id="p1", start="2026-01-01", description="x")
    projected = project_fields(record, frozenset({"start", "not_a_field"}))
    assert projected == {"start": "2026-01-01"}
