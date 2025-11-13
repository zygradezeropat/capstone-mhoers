from __future__ import annotations

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction

from accounts.models import BHWRegistration, Doctors, Nurses
from referrals.utils import send_sms_iprog


def _mark_transition(instance, model_cls):
    """Compute whether status transitions to APPROVED on this save."""
    became_approved = False
    if getattr(instance, model_cls._meta.pk.attname, None):
        try:
            # Load previous version from DB to compare
            prev = model_cls.objects.get(pk=getattr(instance, model_cls._meta.pk.attname))
            prev_status = getattr(prev, "status", None)
        except model_cls.DoesNotExist:
            prev_status = None
    else:
        prev_status = None

    curr_status = getattr(instance, "status", None)
    if prev_status != "APPROVED" and curr_status == "APPROVED":
        became_approved = True
    instance._became_approved = became_approved


@receiver(pre_save, sender=BHWRegistration)
def _bhw_pre_save(sender, instance: BHWRegistration, **kwargs):
    _mark_transition(instance, BHWRegistration)


@receiver(pre_save, sender=Doctors)
def _doc_pre_save(sender, instance: Doctors, **kwargs):
    _mark_transition(instance, Doctors)


@receiver(pre_save, sender=Nurses)
def _nurse_pre_save(sender, instance: Nurses, **kwargs):
    _mark_transition(instance, Nurses)


def _send_approval_sms_async(phone_number: str, first_name: str, last_name: str):
    message = (
        "Your Account has been approved, You Can Now Log in by Using the Correct Credentials"
    )
    # Fire-and-forget; result is not used here
    send_sms_iprog(phone_number, first_name, last_name, message=message, sender_id="MHO-NewCorella")


@receiver(post_save, sender=BHWRegistration)
def _bhw_post_save(sender, instance: BHWRegistration, created: bool, **kwargs):
    if getattr(instance, "_became_approved", False):
        phone = (instance.phone or "").strip()
        if phone:
            transaction.on_commit(lambda: _send_approval_sms_async(phone, instance.first_name or "", instance.last_name or ""))


@receiver(post_save, sender=Doctors)
def _doc_post_save(sender, instance: Doctors, created: bool, **kwargs):
    if getattr(instance, "_became_approved", False):
        phone = (instance.phone or "").strip()
        if phone:
            transaction.on_commit(lambda: _send_approval_sms_async(phone, instance.first_name or "", instance.last_name or ""))


@receiver(post_save, sender=Nurses)
def _nurse_post_save(sender, instance: Nurses, created: bool, **kwargs):
    if getattr(instance, "_became_approved", False):
        phone = (instance.phone or "").strip()
        if phone:
            transaction.on_commit(lambda: _send_approval_sms_async(phone, instance.first_name or "", instance.last_name or ""))


