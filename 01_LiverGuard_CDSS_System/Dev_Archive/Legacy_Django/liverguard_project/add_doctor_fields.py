"""
Script to add password and last_login fields to doctor_profiles table
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'liverguard_project.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check if password column exists
    cursor.execute("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'LiverGuard'
        AND TABLE_NAME = 'doctor_profiles'
        AND COLUMN_NAME = 'password'
    """)
    password_exists = cursor.fetchone()[0]

    if not password_exists:
        print("Adding password column to doctor_profiles...")
        cursor.execute("""
            ALTER TABLE doctor_profiles
            ADD COLUMN password VARCHAR(128) NULL
            AFTER doctor_id
        """)
        print("Password column added successfully!")
    else:
        print("Password column already exists.")

    # Check if last_login column exists
    cursor.execute("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'LiverGuard'
        AND TABLE_NAME = 'doctor_profiles'
        AND COLUMN_NAME = 'last_login'
    """)
    last_login_exists = cursor.fetchone()[0]

    if not last_login_exists:
        print("Adding last_login column to doctor_profiles...")
        cursor.execute("""
            ALTER TABLE doctor_profiles
            ADD COLUMN last_login DATETIME NULL
            AFTER position
        """)
        print("Last_login column added successfully!")
    else:
        print("Last_login column already exists.")

print("\nAll done! Doctor profiles table has been updated.")
