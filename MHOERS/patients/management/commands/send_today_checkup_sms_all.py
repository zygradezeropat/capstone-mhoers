from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from patients.models import Patient, Medical_History
from referrals.utils import send_sms_iprog


class Command(BaseCommand):
    help = "Send SMS reminders to patients with follow-up scheduled today."

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

    def handle(self, *args, **options):
        today = timezone.localdate()
        facility_id = options.get("facility_id")
        sender_id = options.get("sender_id") or "MHO-NewCorella"
        dry_run = options.get("dry_run")

        # Find medical histories with follow-up today
        mh_qs = Medical_History.objects.filter(followup_date=today)
        if facility_id:
            mh_qs = mh_qs.filter(patient_id__facility_id=facility_id)

        # Collect unique patients to avoid duplicate sends
        patient_ids = (
            mh_qs.values_list("patient_id__patients_id", flat=True).distinct()
        )

        count = 0
        sent = 0
        for pid in patient_ids:
            count += 1
            try:
                patient = Patient.objects.get(patients_id=pid)
            except Patient.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Skip missing patient id={pid}"))
                continue

            if dry_run:
                self.stdout.write(
                    f"DRY-RUN: would send to {patient.first_name} {patient.last_name} ({patient.p_number})"
                )
                continue

            # Fetch today's medical history to include advice if available
            mh_today = (
                Medical_History.objects.filter(patient_id=patient, followup_date=today)
                .order_by("-history_id")
                .first()
            )
            advice_text = (mh_today.advice or "").strip() if mh_today else ""
            if advice_text:
                # Keep message concise; truncate long advice
                trimmed_advice = (advice_text[:200] + "…") if len(advice_text) > 200 else advice_text
                message = (
                    f"Hi {patient.first_name} {patient.last_name}, reminder: {trimmed_advice} ."
                )
            else:
                message = (
                    f"Hi {patient.first_name} {patient.last_name}, this is a reminder of your medical check-up scheduled today."
                )
            result = send_sms_iprog(
                patient.p_number,
                patient.first_name,
                patient.last_name,
                message=message,
                sender_id=sender_id,
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
            self.stdout.write(self.style.NOTICE(f"DRY-RUN total due today: {count}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Done. Due: {count}, Sent: {sent}"))


