# models.py

from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils import timezone

class UploadSession(models.Model):
    customer_name = models.CharField(max_length=255)
    balance       = models.DecimalField(
                       max_digits=12,
                       decimal_places=2,
                       validators=[MinValueValidator(Decimal('0.00'))]
                     )
    created_at    = models.DateTimeField(auto_now_add=True)
    report_pdf    = models.FileField(upload_to="reports/", blank=True, null=True)

    def __str__(self):
        return f"Session {self.id} @ {self.created_at}"


class Cheque(models.Model):
    session       = models.ForeignKey(
                      UploadSession,
                      on_delete=models.CASCADE,
                      related_name="cheques"
                    )
    customer_name = models.CharField(max_length=255)
    image         = models.ImageField(upload_to="cheque_uploads/")
    extracted_amt = models.DecimalField(
                      max_digits=12,
                      decimal_places=2,
                      default=Decimal("0.00")
                    )
    status        = models.CharField(
                      max_length=20,
                      choices=[
                        ("accepted",  "Accepted"),
                        ("discarded", "Discarded"),
                        ("flagged",   "Flagged")
                      ],
                      default="flagged"
                    )
    reason        = models.TextField(blank=True)
    image_hash    = models.CharField(max_length=64, blank=True)
    created_at    = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Auto‐populate customer name from session
        if not self.customer_name:
            self.customer_name = self.session.customer_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cheque {self.id} [{self.status}]"
