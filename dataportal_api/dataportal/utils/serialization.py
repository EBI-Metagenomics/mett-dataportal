"""Utility helpers for serializing API responses into alternate formats."""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any, Dict, List, Sequence

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def _flatten_record(record: Any) -> Dict[str, Any]:
    """Convert supported record types into a flat dictionary."""

    if record is None:
        return {}

    if isinstance(record, dict):
        return record

    if isinstance(record, BaseModel):
        return record.model_dump()

    if hasattr(record, "dict") and callable(getattr(record, "dict")):
        return record.dict()

    if hasattr(record, "__dict__"):
        return {key: value for key, value in vars(record).items() if not key.startswith("_")}

    return {"value": record}


def _format_cell(value: Any) -> str:
    """Convert complex cell values into TSV-safe text."""

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return str(value)

    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _is_array_of_objects(value: Any) -> bool:
    """Check if a value is a non-empty array/list of objects (dicts or BaseModel instances)."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False

    if len(value) == 0:
        return False

    # Check if first element is an object-like structure
    first = value[0]
    return isinstance(first, (dict, BaseModel)) or (
        hasattr(first, "__dict__") and not isinstance(first, (str, int, float, bool))
    )


def _denormalize_record(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Denormalize a record by expanding nested arrays into separate rows.

    For each field that contains an array of objects, creates one row per array element,
    copying parent fields and flattening nested object fields.

    Example:
        Input: {"gene": "A", "data": [{"x": 1}, {"x": 2}]}
        Output: [
            {"gene": "A", "x": 1},
            {"gene": "A", "x": 2}
        ]

    If multiple fields contain arrays, creates a cartesian product of all combinations.
    """
    # Find all fields that are arrays of objects
    array_fields: List[tuple[str, List[Any]]] = []
    base_fields: Dict[str, Any] = {}

    for key, value in record.items():
        if _is_array_of_objects(value):
            array_fields.append((key, value))
        else:
            base_fields[key] = value

    # If no arrays found, return single row
    if not array_fields:
        return [base_fields]

    # Expand arrays: create one row per combination
    # Start with base fields
    rows = [base_fields.copy()]

    for field_name, array_value in array_fields:
        new_rows = []
        for row in rows:
            for array_item in array_value:
                # Flatten the nested object
                nested = _flatten_record(array_item)
                # Merge with parent row (nested fields override if same name)
                expanded_row = {**row, **nested}
                new_rows.append(expanded_row)
        rows = new_rows

    return rows


def _coerce_iterable(data: Any) -> List[Dict[str, Any]]:
    """Prepare a list of dictionaries from arbitrary API data payloads."""

    if data is None:
        return []

    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        records = [_flatten_record(item) for item in data]
        # Denormalize each record to expand nested arrays
        denormalized = []
        for record in records:
            denormalized.extend(_denormalize_record(record))
        return denormalized

    if isinstance(data, dict) and "data" in data and isinstance(data["data"], Sequence):
        records = [_flatten_record(item) for item in data["data"]]
        # Denormalize each record to expand nested arrays
        denormalized = []
        for record in records:
            denormalized.extend(_denormalize_record(record))
        return denormalized

    if isinstance(data, BaseModel):
        record = _flatten_record(data)
        return _denormalize_record(record)

    record = _flatten_record(data)
    return _denormalize_record(record)


def serialize_to_tsv(data: Any) -> str:
    """Serialize API response data into a TSV string.

    The serializer automatically denormalizes nested arrays of objects by expanding
    them into separate rows. For each field containing an array of objects, one row
    is created per array element, with parent fields repeated and nested object fields
    flattened and merged.

    Example:
        Input: [{"gene": "A", "data": [{"x": 1}, {"x": 2}]}]
        Output TSV:
            gene    x
            A       1
            A       2

    If multiple fields contain arrays, a cartesian product is created (all combinations).
    Column order is preserved as encountered.
    """

    rows = _coerce_iterable(data)

    if not rows:
        logger.debug("serialize_to_tsv: no rows to serialize")
        return ""

    fieldnames: List[str] = []
    seen_fields = set()
    for row in rows:
        for key in row.keys():
            if key not in seen_fields:
                seen_fields.add(key)
                fieldnames.append(key)

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        delimiter="\t",
        extrasaction="ignore",
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writeheader()
    for row in rows:
        writer.writerow({key: _format_cell(row.get(key)) for key in fieldnames})

    return buffer.getvalue()


__all__ = ["serialize_to_tsv"]
