"""Loads schema JSON templates used to shape per-document-type extractions.

The schemas live as checked-in JSON files under Schema_JSON/ and are populated
by the per-type extraction prompts. Loading at import time keeps runtime
deterministic w.r.t. the schema files in the repo."""

import json
from pathlib import Path


_SCHEMA_DIR = Path(__file__).parent / "Schema_JSON"

_SCHEMA_FILES = {
    "policy_wording": "policy_wordings.json",
    "brochure": "policy_brochure.json",
    "group_policy": "group_policy_schema_template.json",
    "rejection_letter": "claim_rejection_schema_template.json",
}


def _load_schema(filename: str) -> dict:
    with open(_SCHEMA_DIR / filename, "r") as f:
        return json.load(f)


SCHEMAS: dict[str, dict] = {
    doc_type: _load_schema(filename) for doc_type, filename in _SCHEMA_FILES.items()
}


def schema_as_prompt_block(doc_type: str) -> str:
    """Render a schema as a JSON block suitable for inlining into a prompt."""
    return json.dumps(SCHEMAS[doc_type], indent=2)
