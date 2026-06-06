"""
Centralized data file writer that enforces strict self-documenting naming
conventions and generates sidecar metadata (.meta.json) files.
"""

import datetime
import json
import pathlib
import re
from typing import Any

from onet_role_dna.hashing import compute_sha256

PROJECT_REGEX = re.compile(r"^[a-z0-9-]+$")
CONTENT_REGEX = re.compile(r"^[a-z0-9-]+$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_REGEX = re.compile(r"^v\d+\.\d+\.\d+$")


def serialize_payload(data: Any, ext: str) -> bytes:
    """
    Serializes data to bytes based on the file extension.
    If data is already a bytes object, returns it directly.
    """
    if isinstance(data, bytes):
        return data

    ext_clean = ext.lower().lstrip(".")
    if ext_clean == "jsonl":
        if not isinstance(data, list):
            raise ValueError("Data for JSONL must be a list of serializeable objects.")
        lines = []
        for item in data:
            lines.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return "\n".join(lines).encode("utf-8") + b"\n"
    elif ext_clean == "json":
        return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    elif ext_clean == "csv":
        # Dynamic check for pandas DataFrame
        try:
            import pandas as pd
            is_df = isinstance(data, pd.DataFrame)
        except ImportError:
            is_df = False

        if is_df:
            import pandas as pd
            assert isinstance(data, pd.DataFrame)
            df_sorted = data.reindex(sorted(data.columns), axis=1)
            return df_sorted.to_csv(index=False).encode("utf-8")

        if isinstance(data, list):
            if not data:
                return b""
            import csv
            import io
            output = io.StringIO()
            headers = sorted(list(data[0].keys()))
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow({k: row.get(k, "") for k in headers})
            return output.getvalue().encode("utf-8")
        raise ValueError("Unsupported data type for CSV serialization.")
    elif ext_clean == "parquet":
        try:
            import pandas as pd
            is_df = isinstance(data, pd.DataFrame)
        except ImportError:
            is_df = False

        if is_df:
            import pandas as pd
            assert isinstance(data, pd.DataFrame)
            df_sorted = data.reindex(sorted(data.columns), axis=1)
            return df_sorted.to_parquet(index=False)
        raise ValueError("Data for Parquet must be a pandas DataFrame, and pandas/pyarrow must be installed.")
    else:
        # Generic bytes/string fallback
        from onet_role_dna.hashing import serialize_data
        return serialize_data(data)


def write_data_file(
    directory: str | pathlib.Path,
    project: str,
    content: str,
    version: str,
    data: Any,
    ext: str,
    date: str | None = None,
) -> pathlib.Path:
    """
    Validates, serializes, hashes, and writes the data to the naming pattern.
    Also creates a .meta.json sidecar file in the same directory.
    """
    dir_path = pathlib.Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    if date is None:
        date = datetime.date.today().isoformat()

    # Enforce strict naming rules (Fail Fast)
    if not PROJECT_REGEX.match(project):
        raise ValueError(f"Invalid project '{project}': must be lowercase, alphanumeric, hyphens only.")
    if not CONTENT_REGEX.match(content):
        raise ValueError(f"Invalid content '{content}': must be lowercase, alphanumeric, hyphens only.")
    if not DATE_REGEX.match(date):
        raise ValueError(f"Invalid date '{date}': must be in YYYY-MM-DD format.")
    if not VERSION_REGEX.match(version):
        raise ValueError(f"Invalid version '{version}': must be in vX.Y.Z format.")

    ext_clean = ext.lower().lstrip(".")
    if not ext_clean:
        raise ValueError("Extension cannot be empty.")

    # 1. Serialize data to bytes
    serialized_bytes = serialize_payload(data, ext_clean)

    # 2. Compute stable SHA-256
    full_sha = compute_sha256(serialized_bytes)
    hash8 = full_sha[:8]

    # 3. Construct filename conforming to {project}_{content}_{date}_v{version}_{hash8}.{ext}
    filename = f"{project}_{content}_{date}_{version}_{hash8}.{ext_clean}"
    target_path = dir_path / filename

    # 4. Write data file
    target_path.write_bytes(serialized_bytes)

    # 5. Determine row count if applicable
    row_count = None
    if isinstance(data, list):
        row_count = len(data)
    else:
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                row_count = len(data)
        except ImportError:
            pass

    # 6. Construct and write sidecar metadata
    meta = {
        "project": project,
        "content": content,
        "date": date,
        "version": version,
        "hash8": hash8,
        "sha256": full_sha,
        "ext": ext_clean,
        "filename": filename,
        "size_bytes": len(serialized_bytes),
        "row_count": row_count,
    }

    meta_path = dir_path / f"{filename}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    return target_path


if __name__ == "__main__":
    import shutil
    print("Running Phase 2 file writer and metadata sidecar self-test...")

    test_dir = pathlib.Path("data_test_tmp")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    try:
        # Sample test data
        test_data = [
            {"id": 1, "occupation": "Software Engineer", "code": "15-1132"},
            {"id": 2, "occupation": "Data Scientist", "code": "15-1111"}
        ]

        # Write test JSONL file
        written_file = write_data_file(
            directory=test_dir,
            project="onet",
            content="role-dna-full-profiles",
            version="v0.1.0",
            data=test_data,
            ext="jsonl",
            date="2026-06-05"
        )

        print(f"Written file path: {written_file}")

        # Compute dynamic expected name for assertion stability
        test_bytes = serialize_payload(test_data, "jsonl")
        expected_hash = compute_sha256(test_bytes)[:8]
        expected_name = f"onet_role-dna-full-profiles_2026-06-05_v0.1.0_{expected_hash}.jsonl"

        assert written_file.name == expected_name, (
            f"Filename mismatch! Expected {expected_name}, got {written_file.name}"
        )

        # Verify sidecar metadata exists
        meta_file = test_dir / f"{expected_name}.meta.json"
        assert meta_file.exists(), f"Metadata sidecar {meta_file} was not created!"

        # Verify metadata contents
        with open(meta_file, encoding="utf-8") as f:
            metadata = json.load(f)

        assert metadata["project"] == "onet"
        assert metadata["content"] == "role-dna-full-profiles"
        assert metadata["date"] == "2026-06-05"
        assert metadata["version"] == "v0.1.0"
        assert metadata["hash8"] == expected_hash
        assert metadata["ext"] == "jsonl"
        assert metadata["filename"] == expected_name
        assert metadata["row_count"] == 2
        assert len(metadata["sha256"]) == 64

        print("All Phase 2 writer and sidecar tests passed successfully!")
    finally:
        # Clean up
        if test_dir.exists():
            shutil.rmtree(test_dir)
