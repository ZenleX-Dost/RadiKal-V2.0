"""
Database migration script to create missing custom defect tables.
"""

import sqlite3
from pathlib import Path

def migrate():
    db_path = Path(__file__).parent / "data" / "radikal.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    print(f"Migrating database at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {t[0] for t in cursor.fetchall()}
    print(f"Existing tables: {existing_tables}")
    
    # Create custom_defect_types table
    if "custom_defect_types" not in existing_tables:
        cursor.execute("""
            CREATE TABLE custom_defect_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                code VARCHAR NOT NULL UNIQUE,
                description TEXT,
                severity_default VARCHAR DEFAULT 'medium',
                expected_features TEXT,
                color VARCHAR DEFAULT '#808080',
                compliance_standards TEXT,
                min_samples_required INTEGER DEFAULT 50,
                current_sample_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                requires_retraining BOOLEAN DEFAULT 1,
                created_by VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created custom_defect_types table")
    
    # Create training_samples table
    if "training_samples" not in existing_tables:
        cursor.execute("""
            CREATE TABLE training_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_type_id INTEGER REFERENCES custom_defect_types(id),
                image_path VARCHAR,
                image_id VARCHAR,
                annotations TEXT,
                annotation_format VARCHAR DEFAULT 'bbox',
                source VARCHAR DEFAULT 'manual',
                quality_score FLOAT DEFAULT 1.0,
                training_set VARCHAR DEFAULT 'train',
                labeled_by VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created training_samples table")
    
    # Create model_versions table
    if "model_versions" not in existing_tables:
        cursor.execute("""
            CREATE TABLE model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_number VARCHAR NOT NULL,
                model_path VARCHAR,
                training_dataset_id INTEGER,
                base_model VARCHAR DEFAULT 'yolov8s-cls',
                architecture VARCHAR DEFAULT 'yolov8',
                accuracy FLOAT,
                precision_score FLOAT,
                recall FLOAT,
                f1_score FLOAT,
                map50 FLOAT,
                map50_95 FLOAT,
                deployment_status VARCHAR DEFAULT 'trained',
                is_active BOOLEAN DEFAULT 0,
                supports_custom_types BOOLEAN DEFAULT 0,
                custom_types_included TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deployed_at TIMESTAMP
            )
        """)
        print("Created model_versions table")
    
    # Create training_datasets table
    if "training_datasets" not in existing_tables:
        cursor.execute("""
            CREATE TABLE training_datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                description TEXT,
                dataset_path VARCHAR,
                total_images INTEGER DEFAULT 0,
                train_images INTEGER DEFAULT 0,
                val_images INTEGER DEFAULT 0,
                test_images INTEGER DEFAULT 0,
                class_distribution TEXT,
                includes_custom_types BOOLEAN DEFAULT 0,
                custom_types_included TEXT,
                augmentation_config TEXT,
                created_by VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created training_datasets table")
    
    # Create training_jobs table
    if "training_jobs" not in existing_tables:
        cursor.execute("""
            CREATE TABLE training_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version_id INTEGER REFERENCES model_versions(id),
                job_type VARCHAR DEFAULT 'fine_tuning',
                status VARCHAR DEFAULT 'pending',
                hyperparameters TEXT,
                total_epochs INTEGER DEFAULT 100,
                current_epoch INTEGER DEFAULT 0,
                progress_percent FLOAT DEFAULT 0,
                latest_train_loss FLOAT,
                latest_val_loss FLOAT,
                latest_accuracy FLOAT,
                latest_map50 FLOAT,
                estimated_time_remaining_minutes INTEGER,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        print("Created training_jobs table")
    
    # Create active_learning_queue table
    if "active_learning_queue" not in existing_tables:
        cursor.execute("""
            CREATE TABLE active_learning_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER REFERENCES analyses(id),
                uncertainty_score FLOAT,
                priority_score FLOAT,
                selection_method VARCHAR DEFAULT 'uncertainty',
                suggested_defect_types TEXT,
                status VARCHAR DEFAULT 'pending',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP
            )
        """)
        print("Created active_learning_queue table")
    
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
