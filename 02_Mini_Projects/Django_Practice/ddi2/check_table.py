import os
import django

os.chdir(r'c:\ddi\cdss_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DESCRIBE django_1pj_doctorprofile;")
    columns = cursor.fetchall()
    print("\n=== django_1pj_doctorprofile 테이블 구조 ===")
    for col in columns:
        print(col)
