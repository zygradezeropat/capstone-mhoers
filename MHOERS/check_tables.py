#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MHOERS.settings')
django.setup()

from django.db import connection

def check_tables():
    with connection.cursor() as cursor:
        # Check if accounts tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'accounts_%'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print("Accounts tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        if not tables:
            print("  No accounts tables found!")
        
        # Check all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        all_tables = cursor.fetchall()
        
        print(f"\nAll tables in database ({len(all_tables)} total):")
        for table in all_tables:
            print(f"  - {table[0]}")

if __name__ == "__main__":
    check_tables()

