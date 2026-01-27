# Manual migration to add user_id column to DoctorProfile
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_1pj', '0003_drug_druginteraction_monitoring'),
    ]

    operations = [
        # Step 1: Add user_id column as nullable first
        migrations.RunSQL(
            sql="""
                ALTER TABLE django_1pj_doctorprofile
                ADD COLUMN user_id INT NULL UNIQUE;
            """,
            reverse_sql="""
                ALTER TABLE django_1pj_doctorprofile
                DROP COLUMN user_id;
            """
        ),
        # Step 2: Add foreign key constraint
        migrations.RunSQL(
            sql="""
                ALTER TABLE django_1pj_doctorprofile
                ADD CONSTRAINT django_1pj_doctorprofile_user_id_fk
                FOREIGN KEY (user_id) REFERENCES auth_user(id)
                ON DELETE CASCADE;
            """,
            reverse_sql="""
                ALTER TABLE django_1pj_doctorprofile
                DROP FOREIGN KEY django_1pj_doctorprofile_user_id_fk;
            """
        ),
        # Step 3: Make it NOT NULL after data is populated (manual step required)
        # migrations.RunSQL(
        #     sql="""
        #         ALTER TABLE django_1pj_doctorprofile
        #         MODIFY COLUMN user_id INT NOT NULL;
        #     """,
        #     reverse_sql="""
        #         ALTER TABLE django_1pj_doctorprofile
        #         MODIFY COLUMN user_id INT NULL;
        #     """
        # ),
    ]
