from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('referrals', '0016_alter_referral_followup_date'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_referral_status ON referrals_referral(status);",
            "DROP INDEX IF EXISTS idx_referral_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_referral_created_at ON referrals_referral(created_at);",
            "DROP INDEX IF EXISTS idx_referral_created_at;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_referral_user_status ON referrals_referral(user_id, status);",
            "DROP INDEX IF EXISTS idx_referral_user_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_patient_user ON patients_patient(user_id);",
            "DROP INDEX IF EXISTS idx_patient_user;"
        ),
    ]
