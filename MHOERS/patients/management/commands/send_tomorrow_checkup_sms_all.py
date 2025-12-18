from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from patients.models import Patient, Medical_History, SMSReminderLog
from referrals.utils import send_sms_iprog


class Command(BaseCommand):
    help = "Send SMS reminders to patients with follow-up scheduled tomorrow (with duplicate prevention)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--facility-id",
            type=int,
            dest="facility_id",
            help="Only send for patients in this facility ID.",
        )
        parser.add_argument(
            "--sender-id",
            type=str,
            dest="sender_id",
            help="Optional sender ID if enabled on your IPROG account.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="List targets without sending.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            help="Force send even if already sent (not recommended).",
        )

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + timedelta(days=1)
        facility_id = options.get("facility_id")
        sender_id = options.get("sender_id") or "MHO-NewCorella"
        dry_run = options.get("dry_run")
        force = options.get("force", False)

        # Find medical histories with follow-up tomorrow
        mh_qs = Medical_History.objects.filter(followup_date=tomorrow)
        if facility_id:
            mh_qs = mh_qs.filter(patient_id__facility_id=facility_id)

        # Collect unique patients to avoid duplicate sends
        patient_ids = (
            mh_qs.values_list("patient_id__patients_id", flat=True).distinct()
        )

        count = 0
        sent = 0
        skipped = 0
        
        for pid in patient_ids:
            count += 1
            try:
                patient = Patient.objects.get(patients_id=pid)
            except Patient.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Skip missing patient id={pid}"))
                continue

            # Check if already sent (unless force)
            if not force:
                already_sent = SMSReminderLog.objects.filter(
                    patient=patient,
                    followup_date=tomorrow,
                    reminder_type='tomorrow'
                ).exists()
                
                if already_sent:
                    skipped += 1
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f"SKIP (already sent): {patient.first_name} {patient.last_name}"
                            )
                        )
                    continue

            if dry_run:
                self.stdout.write(
                    f"DRY-RUN: would send to {patient.first_name} {patient.last_name} ({patient.p_number})"
                )
                continue

            # Fetch tomorrow's medical history
            mh_tomorrow = (
                Medical_History.objects.filter(patient_id=patient, followup_date=tomorrow)
                .order_by("-history_id")
                .first()
            )
            advice_text = (mh_tomorrow.advice or "").strip() if mh_tomorrow else ""
            tomorrow_formatted = tomorrow.strftime('%B %d, %Y')
            
            if advice_text:
                trimmed_advice = (advice_text[:200] + "…") if len(advice_text) > 200 else advice_text
                message = (
                    f"Hi {patient.first_name} {patient.last_name}, reminder for tomorrow ({tomorrow_formatted}): {trimmed_advice} ."
                )
            else:
                message = (
                    f"Hi {patient.first_name} {patient.last_name}, this is a reminder of your medical check-up scheduled tomorrow ({tomorrow_formatted})."
                )
            
            result = send_sms_iprog(
                patient.p_number,
                patient.first_name,
                patient.last_name,
                message=message,
                sender_id=sender_id,
            )
            
            # Log the SMS attempt
            log_entry, created = SMSReminderLog.objects.get_or_create(
                patient=patient,
                followup_date=tomorrow,
                reminder_type='tomorrow',
                defaults={
                    'medical_history': mh_tomorrow,
                    'message': message,
                    'status': 'sent' if result.get("ok") else 'failed'
                }
            )
            
            if result.get("ok"):
                sent += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Sent to {patient.first_name} {patient.last_name}: {result.get('status_code')}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed for {patient.first_name} {patient.last_name}: {result.get('error')}"
                    )
                )

        if dry_run:
            self.stdout.write(self.style.NOTICE(f"DRY-RUN total due tomorrow: {count}"))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. Due tomorrow: {count}, Sent: {sent}, Skipped (already sent): {skipped}"
                )
            )








