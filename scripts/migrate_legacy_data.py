"""
Utility script to migrate legacy data files in 'data/' to the conforming
strict naming standard with sidecar files, backing up originals safely.
"""

import datetime
import pathlib
import shutil

from onet_role_dna.writer import write_data_file


def migrate_legacy_files():
    data_dir = pathlib.Path("data")
    backup_dir = data_dir / "legacy_backup"
    backup_dir.mkdir(exist_ok=True)

    print("Beginning migration of legacy files in 'data/' to compliant format...")

    migrated_count = 0

    for file_path in data_dir.iterdir():
        # Only process files directly in data/ (skips subdirectories like hf_occupations and legacy_backup)
        if not file_path.is_file():
            continue

        # Skip system, hidden, or markdown files
        if file_path.name.startswith(".") or file_path.name == "README.md":
            continue

        print(f"\nProcessing legacy file: {file_path.name}")

        # 1. Generate clean content slug: replace underscores with hyphens and lowercase
        original_stem = file_path.stem
        ext = file_path.suffix.lstrip(".")
        
        content_slug = original_stem.replace("_", "-").lower()
        # Clean any double hyphens if they occur
        content_slug = "-".join([p for p in content_slug.split("-") if p])

        # 2. Extract original file modification date to maintain timeline integrity
        mtime = file_path.stat().st_mtime
        file_date = datetime.date.fromtimestamp(mtime).isoformat()

        # 3. Read exact raw bytes (preserves Parquet, CSV, msgpack, DB integrity perfectly)
        file_bytes = file_path.read_bytes()

        # 4. Write compliant file and sidecar
        try:
            new_path = write_data_file(
                directory=data_dir,
                project="onet",
                content=content_slug,
                version="v0.1.0",
                data=file_bytes,
                ext=ext,
                date=file_date
            )
            print(f"  -> Converted to: {new_path.name}")
            print(f"  -> Created sidecar: {new_path.name}.meta.json")

            # 5. Move original legacy file to backup directory
            dest_backup = backup_dir / file_path.name
            shutil.move(str(file_path), str(dest_backup))
            print(f"  -> Safely backed up: legacy_backup/{file_path.name}")
            migrated_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to migrate {file_path.name}: {e}")

    print("\n--- Migration Completed ---")
    print(f"Successfully migrated {migrated_count} files.")
    print("All original legacy files have been backed up to 'data/legacy_backup/'.")


if __name__ == "__main__":
    migrate_legacy_files()
