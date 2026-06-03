#!/usr/bin/env python3
"""
Multi-format converter for O*NET occupation profiles
Converts full_profiles.jsonl to CSV, Parquet, HuggingFace Dataset, SQLite, MessagePack, and LLM formats
"""

import json
import pandas as pd
import sqlite3
import msgpack
from pathlib import Path
import sys

def load_profiles(filepath='full_profiles.jsonl'):
    """Load all profiles from JSONL file"""
    profiles = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                profiles.append(json.loads(line))
    return profiles

def create_flattened_dataframe(profiles):
    """Create flattened DataFrame for tabular formats"""
    rows = []
    for profile in profiles:
        code = profile.get('code')
        details = profile.get('details', {})
        
        row = {
            'soc_code': code,
            'title': profile.get('title'),
            'description': profile.get('description'),
            'incomplete': profile.get('incomplete', False),
            'num_tasks': len(details.get('tasks', [])),
            'num_skills': len(details.get('skills', [])),
            'num_knowledge': len(details.get('knowledge', [])),
            'num_abilities': len(details.get('abilities', [])),
            'num_work_activities': len(details.get('work_activities', [])),
            'num_work_styles': len(details.get('work_styles', [])),
            'num_education': len(details.get('education', [])),
            'has_job_zone': 1 if details.get('job_zone') else 0,
            'num_work_context': len(details.get('work_context', [])),
            'num_technology_skills': len(details.get('technology_skills', [])),
            'num_hot_technologies': len(details.get('hot_technologies', [])),
            'bright_outlook': 1 if profile.get('bright_outlook') else 0,
        }
        
        # Add average importance scores for rated sections
        for section in ['tasks', 'skills', 'knowledge', 'abilities', 'work_activities', 'work_styles']:
            items = details.get(section, [])
            if items and isinstance(items[0], dict):
                importances = [item.get('importance', 0) for item in items if 'importance' in item]
                if importances:
                    row[f'avg_importance_{section}'] = sum(importances) / len(importances)
                else:
                    row[f'avg_importance_{section}'] = None
            else:
                row[f'avg_importance_{section}'] = None
        
        rows.append(row)
    
    return pd.DataFrame(rows)

def to_csv(profiles, output_path='profiles.csv'):
    """Convert to CSV format"""
    print(f"📄 Converting to CSV: {output_path}")
    df = create_flattened_dataframe(profiles)
    df.to_csv(output_path, index=False)
    print(f"   ✓ {len(profiles)} profiles exported")
    print(f"   ✓ {len(df.columns)} features")
    return output_path

def to_parquet(profiles, output_path='profiles.parquet'):
    """Convert to Parquet format (columnar, compressed)"""
    print(f"📦 Converting to Parquet: {output_path}")
    df = create_flattened_dataframe(profiles)
    df.to_parquet(output_path, compression='snappy', index=False)
    file_size = Path(output_path).stat().st_size / 1024
    print(f"   ✓ {len(profiles)} profiles exported")
    print(f"   ✓ File size: {file_size:.1f} KB")
    return output_path

def to_huggingface_dataset(profiles, output_path='hf_occupations'):
    """Convert to HuggingFace Dataset format"""
    print(f"🤗 Converting to HuggingFace Dataset: {output_path}")
    try:
        from datasets import Dataset
        
        # Create dataset with full profiles and text representations
        data = {
            'code': [],
            'title': [],
            'description': [],
            'text': [],  # For embeddings/LLM
            'profile_json': [],  # Full nested structure
            'incomplete': [],
        }
        
        for profile in profiles:
            code = profile.get('code')
            title = profile.get('title')
            desc = profile.get('description')
            incomplete = profile.get('incomplete', False)
            
            # Create rich text representation for LLMs
            details = profile.get('details', {})
            text_parts = [
                f"Occupation: {title}",
                f"SOC Code: {code}",
                f"Description: {desc}",
                f"Number of tasks: {len(details.get('tasks', []))}",
                f"Number of skills: {len(details.get('skills', []))}",
                f"Number of abilities: {len(details.get('abilities', []))}",
            ]
            
            data['code'].append(code)
            data['title'].append(title)
            data['description'].append(desc)
            data['text'].append('\n'.join(text_parts))
            data['profile_json'].append(json.dumps(profile))
            data['incomplete'].append(incomplete)
        
        dataset = Dataset.from_dict(data)
        dataset.save_to_disk(output_path)
        print(f"   ✓ {len(profiles)} profiles exported")
        print(f"   ✓ Saved to: {output_path}/")
        return output_path
    except ImportError:
        print("   ⚠ HuggingFace datasets not installed. Install with: pip install datasets")
        return None

def to_sqlite(profiles, output_path='profiles.db'):
    """Convert to SQLite database"""
    print(f"🗄️  Converting to SQLite: {output_path}")
    
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    
    # Create profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS occupations (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            incomplete BOOLEAN,
            num_tasks INTEGER,
            num_skills INTEGER,
            num_knowledge INTEGER,
            num_abilities INTEGER,
            num_work_activities INTEGER,
            num_work_styles INTEGER,
            num_education INTEGER,
            num_work_context INTEGER,
            profile_json TEXT
        )
    ''')
    
    # Insert profiles
    for profile in profiles:
        code = profile.get('code')
        details = profile.get('details', {})
        
        cursor.execute('''
            INSERT OR REPLACE INTO occupations 
            (code, title, description, incomplete, num_tasks, num_skills, 
             num_knowledge, num_abilities, num_work_activities, num_work_styles, 
             num_education, num_work_context, profile_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            code,
            profile.get('title'),
            profile.get('description'),
            profile.get('incomplete', False),
            len(details.get('tasks', [])),
            len(details.get('skills', [])),
            len(details.get('knowledge', [])),
            len(details.get('abilities', [])),
            len(details.get('work_activities', [])),
            len(details.get('work_styles', [])),
            len(details.get('education', [])),
            len(details.get('work_context', [])),
            json.dumps(profile)
        ))
    
    # Create detailed tables for each section type
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT,
            occupation_code TEXT,
            name TEXT,
            description TEXT,
            importance INTEGER,
            PRIMARY KEY (id, occupation_code),
            FOREIGN KEY (occupation_code) REFERENCES occupations(code)
        )
    ''')
    
    for profile in profiles:
        code = profile.get('code')
        details = profile.get('details', {})
        
        for skill in details.get('skills', []):
            cursor.execute('''
                INSERT OR REPLACE INTO skills 
                (id, occupation_code, name, description, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                skill.get('id'),
                code,
                skill.get('name'),
                skill.get('description'),
                skill.get('importance')
            ))
    
    conn.commit()
    conn.close()
    
    file_size = Path(output_path).stat().st_size / 1024
    print(f"   ✓ {len(profiles)} profiles exported")
    print(f"   ✓ Tables: occupations, skills")
    print(f"   ✓ File size: {file_size:.1f} KB")
    return output_path

def to_msgpack(profiles, output_path='profiles.msgpack'):
    """Convert to MessagePack format (binary, efficient)"""
    print(f"⚡ Converting to MessagePack: {output_path}")
    
    with open(output_path, 'wb') as f:
        packed = msgpack.packb(profiles, use_bin_type=True)
        f.write(packed)
    
    file_size = Path(output_path).stat().st_size / 1024
    print(f"   ✓ {len(profiles)} profiles exported")
    print(f"   ✓ File size: {file_size:.1f} KB")
    return output_path

def to_llm_instruction_pairs(profiles, output_path='profiles_llm_instructions.jsonl'):
    """Convert to LLM instruction-response pairs"""
    print(f"🤖 Converting to LLM instruction pairs: {output_path}")
    
    instruction_pairs = []
    
    for profile in profiles:
        code = profile.get('code')
        title = profile.get('title')
        desc = profile.get('description')
        details = profile.get('details', {})
        
        # Pair 1: Skills instruction
        if details.get('skills'):
            top_skills = details['skills'][:3]
            skills_text = ', '.join([s.get('name', '') for s in top_skills])
            instruction_pairs.append({
                'instruction': f"What are the top skills for {title} ({code})?",
                'response': f"The top skills for {title} include: {skills_text}. Additional skills available in the full profile.",
                'occupation_code': code,
                'category': 'skills'
            })
        
        # Pair 2: Description instruction
        instruction_pairs.append({
            'instruction': f"Describe the occupation {title}.",
            'response': desc,
            'occupation_code': code,
            'category': 'description'
        })
        
        # Pair 3: Abilities instruction
        if details.get('abilities'):
            top_abilities = details['abilities'][:3]
            abilities_text = ', '.join([a.get('name', '') for a in top_abilities])
            instruction_pairs.append({
                'instruction': f"What abilities are important for {title}?",
                'response': f"Important abilities for {title} include: {abilities_text}.",
                'occupation_code': code,
                'category': 'abilities'
            })
        
        # Pair 4: Work styles instruction
        if details.get('work_styles'):
            top_styles = details['work_styles'][:3]
            styles_text = ', '.join([s.get('name', '') for s in top_styles])
            instruction_pairs.append({
                'instruction': f"What work styles characterize {title}?",
                'response': f"Key work styles for {title}: {styles_text}.",
                'occupation_code': code,
                'category': 'work_styles'
            })
        
        # Pair 5: Task instruction
        if details.get('tasks'):
            sample_task = details['tasks'][0].get('title', '')
            instruction_pairs.append({
                'instruction': f"What is a typical task for {title}?",
                'response': f"A typical task for {title}: {sample_task}",
                'occupation_code': code,
                'category': 'tasks'
            })
    
    with open(output_path, 'w') as f:
        for pair in instruction_pairs:
            f.write(json.dumps(pair) + '\n')
    
    print(f"   ✓ {len(instruction_pairs)} instruction pairs generated")
    print(f"   ✓ Categories: skills, description, abilities, work_styles, tasks")
    return output_path

def to_arrow_ipc(profiles, output_path='profiles.arrow'):
    """Convert to Apache Arrow IPC (columnar format)"""
    print(f"🔀 Converting to Apache Arrow: {output_path}")
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
        
        df = create_flattened_dataframe(profiles)
        table = pa.Table.from_pandas(df)
        
        with open(output_path, 'wb') as sink:
            writer = ipc.new_stream(sink, table.schema)
            writer.write_table(table)
            writer.close()
        
        file_size = Path(output_path).stat().st_size / 1024
        print(f"   ✓ {len(profiles)} profiles exported")
        print(f"   ✓ File size: {file_size:.1f} KB")
        return output_path
    except ImportError:
        print("   ⚠ PyArrow not installed. Install with: pip install pyarrow")
        return None

def generate_format_summary():
    """Print summary of generated formats"""
    print("\n" + "=" * 80)
    print("FORMAT CONVERSION SUMMARY")
    print("=" * 80)
    print("""
Generated Formats:

1. CSV (profiles.csv)
   - Tabular format, human-readable
   - Use for: Excel, pandas, scikit-learn
   
2. Parquet (profiles.parquet)
   - Compressed columnar format
   - Use for: Data lakes, big data pipelines, fast I/O
   
3. HuggingFace Dataset (hf_occupations/)
   - Dataset library format
   - Use for: Transformer models, fine-tuning
   
4. SQLite (profiles.db)
   - Relational database with full JSON storage
   - Use for: SQL queries, feature engineering, data exploration
   
5. MessagePack (profiles.msgpack)
   - Binary serialization format
   - Use for: High-performance APIs, low-latency inference
   
6. LLM Instruction Pairs (profiles_llm_instructions.jsonl)
   - Question-answer pairs in JSONL format
   - Use for: LLM fine-tuning, RAG systems, prompt engineering
   
7. Apache Arrow (profiles.arrow)
   - Columnar in-memory format
   - Use for: Data interchange, zero-copy analytics

Format Characteristics:
┌─────────────────┬──────────────┬────────────────┬──────────────┐
│ Format          │ Compression  │ ML Framework   │ Best For     │
├─────────────────┼──────────────┼────────────────┼──────────────┤
│ CSV             │ None         │ Pandas/Sklearn │ Tabular ML   │
│ Parquet         │ High         │ Spark/Pandas   │ Data lakes   │
│ HuggingFace     │ Medium       │ Transformers   │ LLM/BERT     │
│ SQLite          │ Medium       │ SQL            │ Queries      │
│ MessagePack     │ High         │ APIs           │ Performance  │
│ LLM Pairs       │ None         │ LLM APIs       │ Fine-tuning  │
│ Arrow           │ None         │ Polars/DuckDB  │ Analytics    │
└─────────────────┴──────────────┴────────────────┴──────────────┘

Query Examples:

CSV/Parquet:
  >>> import pandas as pd
  >>> df = pd.read_parquet('profiles.parquet')
  >>> df[df['num_skills'] > 30]

SQLite:
  >>> import sqlite3
  >>> conn = sqlite3.connect('profiles.db')
  >>> pd.read_sql('SELECT * FROM occupations WHERE num_skills > 30', conn)

HuggingFace:
  >>> from datasets import load_from_disk
  >>> ds = load_from_disk('hf_occupations')
  >>> ds.features

LLM Pairs:
  >>> import json
  >>> pairs = [json.loads(line) for line in open('profiles_llm_instructions.jsonl')]
  >>> [p for p in pairs if p['category'] == 'skills'][:3]
    """)

def main():
    print("=" * 80)
    print("O*NET OCCUPATION PROFILES - MULTI-FORMAT CONVERTER")
    print("=" * 80)
    print()
    
    # Load profiles
    print("📥 Loading profiles from full_profiles.jsonl...")
    profiles = load_profiles()
    print(f"   ✓ Loaded {len(profiles)} profiles\n")
    
    # Convert to all formats
    results = {
        'csv': to_csv(profiles),
        'parquet': to_parquet(profiles),
        'huggingface': to_huggingface_dataset(profiles),
        'sqlite': to_sqlite(profiles),
        'msgpack': to_msgpack(profiles),
        'llm_pairs': to_llm_instruction_pairs(profiles),
        'arrow': to_arrow_ipc(profiles),
    }
    
    print("\n" + "=" * 80)
    print("✅ CONVERSION COMPLETE")
    print("=" * 80)
    
    # Print summary
    generate_format_summary()
    
    # List generated files
    print("\nGenerated Files:")
    for fmt, path in results.items():
        if path:
            if Path(path).is_dir():
                print(f"  📁 {path}/ (directory)")
            else:
                size = Path(path).stat().st_size / 1024
                print(f"  📄 {path} ({size:.1f} KB)")
    
    print("\n✨ All formats ready for ML/LLM use!")

if __name__ == '__main__':
    main()
