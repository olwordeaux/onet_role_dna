"""
Standalone directory validator that scans and verifies data files and metadata sidecars
for naming policy compliance and cryptographic integrity.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys
from typing import List

PROJECT_REGEX = re.compile(r"^[a-z0-9-]+$")
CONTENT_REGEX = re.compile(r"^[a-z0-9-]+$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_REGEX = re.compile(r"^v\d+\.\d+\.\d+$")
HASH8_REGEX = re.compile(r"^[a-f0-9]{8}$")

ALLOWED_EXCEPTIONS = {".gitkeep", ".gitignore"}


def validate_date(date_str: str) -> bool:
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def validate_data_file(file_path: pathlib.Path) -> List[str]:
    """
    Validates a data file's name and verifies its content matches the embedded hash.
    """
    errors = []
    filename = file_path.name

    # Check for exactly 4 underscores
    parts = filename.split("_")
    if len(parts) != 5:
        errors.append(
            f"Filename must contain exactly 4 underscores separating 5 units. Found {len(parts) - 1} underscores."
        )
        return errors

    project, content, date, version, hash_ext = parts

    # 1. Project name check
    if not PROJECT_REGEX.match(project):
        errors.append(f"Invalid project slug '{project}': must be lowercase alphanumeric with hyphens only.")

    # 2. Content name check
    if not CONTENT_REGEX.match(content):
        errors.append(f"Invalid content slug '{content}': must be lowercase alphanumeric with hyphens only.")

    # 3. Date check
    if not DATE_REGEX.match(date) or not validate_date(date):
        errors.append(f"Invalid ISO 8601 date '{date}': must be YYYY-MM-DD.")

    # 4. Version check
    if not VERSION_REGEX.match(version):
        errors.append(f"Invalid version '{version}': must match semantic vX.Y.Z pattern.")

    # 5. Hash and extension check
    if "." not in hash_ext:
        errors.append(f"Missing file extension in last component '{hash_ext}'.")
        return errors

    hash8, _ext = hash_ext.split(".", 1)

    if not HASH8_REGEX.match(hash8):
        errors.append(f"Invalid 8-char hash suffix '{hash8}': must be hexadecimal.")

    # 6. Content hash verification
    try:
        file_bytes = file_path.read_bytes()
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        actual_sha = hasher.hexdigest()
        actual_hash8 = actual_sha[:8]

        if actual_hash8 != hash8:
            errors.append(
                f"Content integrity violation: filename hash claims '{hash8}', "
                f"but actual content hashes to '{actual_hash8}' (full: {actual_sha})."
            )
    except Exception as e:
        errors.append(f"Failed to read/hash file contents: {e}")

    return errors


def validate_sidecar_file(meta_path: pathlib.Path) -> List[str]:
    """
    Validates a .meta.json sidecar file against its corresponding data file.
    """
    errors = []

    # Deriving expected data file path (remove '.meta.json' suffix)
    data_filename = meta_path.name[:-10]
    data_path = meta_path.parent / data_filename

    if not data_path.exists():
        errors.append(f"Orphan sidecar file: corresponding data file '{data_filename}' does not exist.")
        return errors

    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    except Exception as e:
        errors.append(f"Failed to load sidecar JSON: {e}")
        return errors

    # Check key fields in sidecar
    required_keys = {"project", "content", "date", "version", "hash8", "sha256", "ext", "filename", "size_bytes"}
    missing_keys = required_keys - set(meta.keys())
    if missing_keys:
        errors.append(f"Sidecar metadata is missing required keys: {missing_keys}")
        return errors

    # Parse filename parts of data file
    parts = data_filename.split("_")
    if len(parts) == 5:
        project, content, date, version, hash_ext = parts
        if "." in hash_ext:
            hash8, ext = hash_ext.split(".", 1)

            # Cross-reference sidecar with parsed naming parts
            if meta["project"] != project:
                errors.append(f"Sidecar project '{meta['project']}' does not match filename project '{project}'.")
            if meta["content"] != content:
                errors.append(f"Sidecar content '{meta['content']}' does not match filename content '{content}'.")
            if meta["date"] != date:
                errors.append(f"Sidecar date '{meta['date']}' does not match filename date '{date}'.")
            if meta["version"] != version:
                errors.append(f"Sidecar version '{meta['version']}' does not match filename version '{version}'.")
            if meta["hash8"] != hash8:
                errors.append(f"Sidecar hash8 '{meta['hash8']}' does not match filename hash8 '{hash8}'.")
            if meta["ext"] != ext:
                errors.append(f"Sidecar ext '{meta['ext']}' does not match filename ext '{ext}'.")
            if meta["filename"] != data_filename:
                errors.append(
                    f"Sidecar filename '{meta['filename']}' does not match actual filename '{data_filename}'."
                )

    # Verify size and hash against actual data file
    try:
        data_bytes = data_path.read_bytes()
        actual_sha = hashlib.sha256(data_bytes).hexdigest()
        actual_size = len(data_bytes)

        if meta["sha256"] != actual_sha:
            errors.append(f"Sidecar sha256 '{meta['sha256']}' does not match actual data file sha256 '{actual_sha}'.")
        if meta["size_bytes"] != actual_size:
            errors.append(
                f"Sidecar size_bytes {meta['size_bytes']} does not match actual data file size {actual_size}."
            )
    except Exception as e:
        errors.append(f"Error reading corresponding data file for sidecar validation: {e}")

    return errors


def validate_directory(directory: str | pathlib.Path) -> bool:
    """
    Scans a directory, validates all files, prints any errors, and returns
    True if all files are fully valid and compliant, False otherwise.
    """
    dir_path = pathlib.Path(directory)
    if not dir_path.is_dir():
        print(f"Error: Target directory '{directory}' does not exist or is not a directory.", file=sys.stderr)
        return False

    all_compliant = True
    scanned_count = 0

    print(f"Scanning directory for naming policy compliance: '{dir_path.resolve()}'")

    for file_path in dir_path.iterdir():
        if not file_path.is_file():
            continue

        filename = file_path.name
        if filename in ALLOWED_EXCEPTIONS:
            continue

        scanned_count += 1
        errors = []

        if filename.endswith(".meta.json"):
            errors = validate_sidecar_file(file_path)
        else:
            errors = validate_data_file(file_path)

        if errors:
            all_compliant = False
            print(f"\n[INVALID] {filename}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK] {filename}")

    print("\n--- Validation Summary ---")
    print(f"Total non-excepted files scanned: {scanned_count}")
    if all_compliant:
        print("Status: SUCCESS. All files comply with the naming and integrity policy.")
    else:
        print("Status: FAILURE. Non-conforming or corrupted files were detected.", file=sys.stderr)

    return all_compliant


def run_self_tests() -> None:
    import shutil
    print("Running Phase 3 validator self-test...")
    test_dir = pathlib.Path("validator_test_tmp")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Create a valid file & sidecar manually
        valid_content = b"valid data contents"
        valid_sha = hashlib.sha256(valid_content).hexdigest()
        valid_hash8 = valid_sha[:8]
        valid_filename = f"onet_valid-test_2026-06-05_v1.0.0_{valid_hash8}.json"

        valid_path = test_dir / valid_filename
        valid_path.write_bytes(valid_content)

        valid_meta = {
            "project": "onet",
            "content": "valid-test",
            "date": "2026-06-05",
            "version": "v1.0.0",
            "hash8": valid_hash8,
            "sha256": valid_sha,
            "ext": "json",
            "filename": valid_filename,
            "size_bytes": len(valid_content)
        }
        valid_meta_path = test_dir / f"{valid_filename}.meta.json"
        valid_meta_path.write_text(json.dumps(valid_meta, indent=2), encoding="utf-8")

        # 2. Create an invalid file with wrong hash in name
        invalid_filename = "onet_invalid-test_2026-06-05_v1.0.0_deadbeef.json"
        invalid_path = test_dir / invalid_filename
        invalid_path.write_bytes(b"some other content")

        # 3. Create a totally non-conforming file
        bad_format_path = test_dir / "completely_invalid_name.txt"
        bad_format_path.write_bytes(b"bad name")

        # Run validation
        print("\n--- Expecting 1 OK file, and 2 INVALID files below ---")
        success = validate_directory(test_dir)

        # The overall validation must fail since there are invalid files
        assert not success, "Validation should have failed but reported success!"

        # Individual file validation assertions
        valid_errors = validate_data_file(valid_path)
        assert len(valid_errors) == 0, f"Expected no errors for valid file, got: {valid_errors}"

        invalid_errors = validate_data_file(invalid_path)
        assert len(invalid_errors) > 0, "Expected errors for invalid hash file, but got none."
        assert any(
            "Content integrity violation" in err for err in invalid_errors
        ), f"Unexpected error msg: {invalid_errors}"

        bad_format_errors = validate_data_file(bad_format_path)
        assert len(bad_format_errors) > 0, "Expected naming error for malformed filename, but got none."

        print("\nAll Phase 3 directory validator self-tests passed successfully!")
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate data files against strict naming and integrity patterns.")
    parser.add_argument("directory", type=str, nargs="?", default="data", help="Directory to scan (default: 'data')")
    parser.add_argument("--self-test", action="store_true", help="Run standalone validation unit tests.")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    success = validate_directory(args.directory)
    sys.exit(0 if success else 1)
