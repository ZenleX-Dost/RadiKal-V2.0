"""
Database Migration: Add New Feature Tables
For: Analytics, Review System, Compliance

Run this script to add the required tables for new features:
- reviews
- review_annotations
- compliance_certificates
- operator_performance

Usage: python backend/scripts/add_feature_tables.py
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "backend/data/radikal.db"

def create_tables():
    """Create all required tables for new features."""
    
    print(f"📊 Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n🔨 Creating tables...")
    
    # 1. Reviews Table
    print("  ✓ Creating 'reviews' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('approved', 'rejected', 'needs_second_opinion')),
            comments TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analysis_history(id)
        )
    """)
    
    # 2. Review Annotations Table
    print("  ✓ Creating 'review_annotations' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            annotation_type TEXT NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        )
    """)
    
    # 3. Compliance Certificates Table
    print("  ✓ Creating 'compliance_certificates' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id TEXT NOT NULL,
            standard TEXT NOT NULL,
            certificate_number TEXT NOT NULL UNIQUE,
            compliant BOOLEAN NOT NULL,
            severity_level TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            valid_until TEXT,
            generated_by TEXT NOT NULL,
            pdf_path TEXT,
            FOREIGN KEY (analysis_id) REFERENCES analysis_history(id)
        )
    """)
    
    # 4. Operator Performance Table
    print("  ✓ Creating 'operator_performance' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operator_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL,
            processing_time_seconds REAL NOT NULL,
            accuracy_score REAL,
            review_status TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analysis_history(id)
        )
    """)
    
    # Create indexes for better query performance
    print("\n📇 Creating indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_analysis_id 
        ON reviews(analysis_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_status 
        ON reviews(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_certificates_analysis_id 
        ON compliance_certificates(analysis_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_certificates_standard 
        ON compliance_certificates(standard)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_operator_performance_operator_id 
        ON operator_performance(operator_id)
    """)
    
    conn.commit()
    print("\n✅ All tables created successfully!")
    
    # Show table info
    print("\n📋 Database Schema:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  • {table[0]}")
    
    conn.close()
    print(f"\n✨ Migration complete! Database: {DB_PATH}\n")

def verify_tables():
    """Verify all tables were created."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    required_tables = [
        'reviews',
        'review_annotations',
        'compliance_certificates',
        'operator_performance'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print("\n🔍 Verification:")
    all_present = True
    for table in required_tables:
        present = table in existing_tables
        status = "✅" if present else "❌"
        print(f"  {status} {table}")
        if not present:
            all_present = False
    
    conn.close()
    return all_present

if __name__ == "__main__":
    print("=" * 60)
    print("RadiKal Feature Tables Migration")
    print("=" * 60)
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"\n⚠️  Database not found: {DB_PATH}")
        print("Please ensure the backend has been initialized first.")
        exit(1)
    
    try:
        create_tables()
        
        if verify_tables():
            print("🎉 All tables verified successfully!\n")
        else:
            print("⚠️  Some tables are missing. Please check the logs.\n")
            
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        exit(1)
