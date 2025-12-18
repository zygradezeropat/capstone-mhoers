from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Medical_History, SMSReminderLog, Patient
from referrals.utils import send_sms_iprog


@receiver(post_save, sender=Medical_History)
def auto_send_followup_sms(sender, instance, created, **kwargs):
    """
    Automatically send SMS when followup_date is set to tomorrow.
    Prevents duplicates using SMSReminderLog.
    Only sends if referral is completed (not pending).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Print to console for immediate debugging (also log)
    print(f"[SMS Signal] Triggered for Medical_History ID: {instance.history_id}")
    
    # Only process if followup_date is set
    if not instance.followup_date:
        msg = f"SMS Signal: No followup_date for Medical_History {instance.history_id}"
        logger.debug(msg)
        print(f"[SMS Signal] {msg}")
        return
    
    tomorrow = timezone.localdate() + timedelta(days=1)
    
    # Normalize followup_date to date (in case it's datetime)
    followup_date_only = instance.followup_date
    # Check if it's a datetime object and convert to date
    from datetime import datetime, date
    if isinstance(followup_date_only, datetime):
        followup_date_only = followup_date_only.date()
    elif not isinstance(followup_date_only, date):
        # If it's neither datetime nor date, try to convert
        try:
            if hasattr(followup_date_only, 'date'):
                followup_date_only = followup_date_only.date()
        except:
            pass
    
    print(f"[SMS Signal] Today: {timezone.localdate()}, Tomorrow: {tomorrow}, Follow-up date: {instance.followup_date} (type: {type(instance.followup_date).__name__}, normalized: {followup_date_only})")
    
    # Only send if followup_date is tomorrow (compare dates, not datetime)
    if followup_date_only != tomorrow:
        msg = f"SMS Signal: followup_date {followup_date_only} (type: {type(followup_date_only).__name__}) is not tomorrow {tomorrow} (type: {type(tomorrow).__name__})"
        logger.debug(msg)
        print(f"[SMS Signal] {msg}")
        return
    
    msg = f"SMS Signal: Processing Medical_History {instance.history_id} with followup_date={instance.followup_date} (tomorrow)"
    logger.info(msg)
    print(f"[SMS Signal] {msg}")
    
    # ✅ Check if referral is completed (not pending)
    # Only send SMS after doctor confirms follow-up, not when BHW creates referral
    if instance.referral_id:
        # Query referral fresh from database to get latest status (avoid stale cache)
        from referrals.models import Referral
        try:
            referral = Referral.objects.get(referral_id=instance.referral_id)
            referral_status = referral.status
            msg = f"SMS Signal: Referral {referral.referral_id} status = {referral_status}"
            logger.info(msg)
            print(f"[SMS Signal] {msg}")
            
            if referral_status != 'completed':
                msg = f"SMS Signal: Skipping - Referral status is '{referral_status}', not 'completed'"
                logger.info(msg)
                print(f"[SMS Signal] {msg}")
                return  # Don't send SMS if referral is not completed yet
        except Referral.DoesNotExist:
            msg = f"SMS Signal: Referral {instance.referral_id} not found - allowing SMS anyway"
            logger.warning(msg)
            print(f"[SMS Signal] {msg}")
    else:
        msg = f"SMS Signal: Medical_History {instance.history_id} has no referral link - allowing SMS anyway"
        logger.warning(msg)
        print(f"[SMS Signal] {msg}")
    
    patient = instance.patient_id
    if not patient:
        msg = f"SMS Signal: No patient found for Medical_History {instance.history_id}"
        logger.warning(msg)
        print(f"[SMS Signal] {msg}")
        return
    
    if not patient.p_number:
        msg = f"SMS Signal: Patient {patient.patients_id} has no phone number"
        logger.warning(msg)
        print(f"[SMS Signal] {msg}")
        return
    
    print(f"[SMS Signal] Patient: {patient.first_name} {patient.last_name}, Phone: {patient.p_number}")
    
    # Check if SMS already sent for this patient and followup_date
    already_sent = SMSReminderLog.objects.filter(
        patient=patient,
        followup_date=followup_date_only,
        reminder_type='tomorrow'
    ).exists()
    
    if already_sent:
        msg = f"SMS Signal: SMS already sent to {patient.first_name} {patient.last_name} for {followup_date_only}"
        print(f"[SMS Signal] {msg}")
        return  # Prevent duplicate
    
    # Use database transaction to prevent race conditions
    try:
        with transaction.atomic():
            # Double-check with lock to prevent race condition
            log_entry, created = SMSReminderLog.objects.get_or_create(
                patient=patient,
                followup_date=followup_date_only,
                reminder_type='tomorrow',
                defaults={
                    'medical_history': instance,
                    'status': 'sent'
                }
            )
            
            if not created:
                return  # Already exists, skip sending
            
            # Prepare message
            advice_text = (instance.advice or "").strip()
            tomorrow_formatted = followup_date_only.strftime('%B %d, %Y')
            
            if advice_text:
                trimmed_advice = (advice_text[:200] + "…") if len(advice_text) > 200 else advice_text
                message = (
                    f"Hi {patient.first_name} {patient.last_name}, reminder for tomorrow ({tomorrow_formatted}): {trimmed_advice} ."
                )
            else:
                message = (
                    f"Hi {patient.first_name} {patient.last_name}, this is a reminder of your medical check-up scheduled tomorrow ({tomorrow_formatted})."
                )
            
            # Send SMS asynchronously (fire-and-forget to avoid blocking)
            print(f"[SMS Signal] ✅ All checks passed! Scheduling SMS send for {patient.first_name} {patient.last_name}")
            transaction.on_commit(
                lambda: _send_sms_async(patient, message, log_entry)
            )
            
    except Exception as e:
        # Log error but don't break the save operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending auto SMS reminder: {e}")


def _send_sms_async(patient, message, log_entry):
    """Send SMS and update log entry"""
    try:
        result = send_sms_iprog(
            patient.p_number,
            patient.first_name,
            patient.last_name,
            message=message,
            sender_id="MHO-NewCorella",
        )
        
        if result.get("ok"):
            log_entry.status = 'sent'
            log_entry.message = message
        else:
            log_entry.status = 'failed'
            log_entry.message = f"Failed: {result.get('error', 'Unknown error')}"
        
        log_entry.save()
    except Exception as e:
        log_entry.status = 'failed'
        log_entry.message = f"Exception: {str(e)}"
        log_entry.save()

