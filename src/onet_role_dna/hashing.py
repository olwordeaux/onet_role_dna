"""
Core serialization and hashing utilities to ensure stable SHA-256 calculations
regardless of dictionary key-ordering or data types.
"""

import hashlib
import json
from typing import Any


class SerializationError(Exception):
    """Raised when data serialization fails or is unsupported."""
    pass


def serialize_data(data: Any) -> bytes:
    """
    Serializes various data types into a deterministic byte stream for stable hashing.

    Supports:
    - bytes: returned as-is.
    - str: encoded as UTF-8.
    - list / dict: serialized to JSON with sorted keys and UTF-8 encoded.
    - pandas.DataFrame: serialized deterministically (if pandas is available).
    """
    if isinstance(data, bytes):
        return data
    elif isinstance(data, str):
        return data.encode("utf-8")
    elif isinstance(data, (dict, list)):
        try:
            # Enforce sorted keys for deterministic JSON serialization
            return json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise SerializationError(f"Failed to serialize list/dict to JSON: {e}") from e

    # Dynamic check for pandas to support DataFrames if installed
    try:
        import pandas as pd
        is_dataframe = isinstance(data, pd.DataFrame)
    except ImportError:
        is_dataframe = False

    if is_dataframe:
        try:
            # Deterministic DataFrame serialization by sorting columns and index
            import pandas as pd
            assert isinstance(data, pd.DataFrame)  # Type narrowing for static analysis
            df_sorted = data.reindex(sorted(data.columns), axis=1)
            json_str = df_sorted.to_json(orient="records", date_format="iso")
            if json_str is None:
                raise SerializationError("DataFrame to_json returned None")
            return json_str.encode("utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to serialize pandas DataFrame: {e}") from e

    # Fallback/catch-all for custom objects
    try:
        if hasattr(data, "to_dict") and callable(data.to_dict):
            return serialize_data(data.to_dict())
        return str(data).encode("utf-8")
    except Exception as e:
        raise SerializationError(f"Unsupported data type for stable serialization: {type(data)}. Error: {e}") from e


def compute_sha256(data: Any) -> str:
    """
    Computes a stable SHA-256 hash of the input data.
    Returns the full 64-character hexadecimal representation.
    """
    serialized = serialize_data(data)
    hasher = hashlib.sha256()
    hasher.update(serialized)
    return hasher.hexdigest()


if __name__ == "__main__":
    print("Running stable SHA-256 calculation and serialization self-test...")

    # Test 1: String hashing
    h1 = compute_sha256("test-string")
    print(f"String hash: {h1}")
    expected_str_hash = "ffe65f1d98fafedea3514adc956c8ada5980c6c5d2552fd61f48401aefd5c00e"
    assert h1 == expected_str_hash, f"String hash mismatch. Expected {expected_str_hash}, got {h1}"

    # Test 2: Dict ordering stability
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    h_d1 = compute_sha256(d1)
    h_d2 = compute_sha256(d2)
    print(f"Dict 1 hash: {h_d1}")
    print(f"Dict 2 hash: {h_d2}")
    assert h_d1 == h_d2, f"Dict hashing is not order-stable! {h_d1} vs {h_d2}"

    print("All Phase 1 serialization and hashing self-tests passed successfully!")
