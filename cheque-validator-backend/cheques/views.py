# views.py

import io
import os
import uuid
import hashlib
import traceback

import cv2
import numpy as np
import torch
from PIL import Image
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from django.core.files.base import ContentFile
from rest_framework import generics, status
from rest_framework.response import Response
from reportlab.lib.pagesizes import letter
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.units import inch

from .models import UploadSession, Cheque
from .serializers import UploadSessionSerializer

# ─── Configuration ───────────────────────────────────────────────────────────────
DEVICE    = None
PROCESSOR = None
MODEL     = None

def load_models():
    global DEVICE, PROCESSOR, MODEL
    if DEVICE is None:
        try:
            DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        except:
            DEVICE = torch.device("cpu")

    if PROCESSOR is None:
        PROCESSOR = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")

    if MODEL is None:
        MODEL = VisionEncoderDecoderModel.from_pretrained(
                  "microsoft/trocr-base-handwritten"
                ).to(DEVICE)


class ChequeUploadView(generics.CreateAPIView):
    serializer_class = UploadSessionSerializer
    queryset         = UploadSession.objects.all()

    def create(self, request, *args, **kwargs):
        try:
            sess_serializer = self.get_serializer(data=request.data)
            sess_serializer.is_valid(raise_exception=True)
            self.session = sess_serializer.save()

            results       = []
            seen          = set()
            remaining     = self.session.balance  # start with full balance

            # ─── Process each uploaded cheque image ─────────────────────
            for img in request.FILES.getlist("cheques"):
                raw = img.read()
                h   = hashlib.sha256(raw).hexdigest()
                img.seek(0)

                entry = {
                    "image_name": img.name,
                    "status":     "pending",
                    "amount":     None,
                    "reason":     None,
                }

                # 1) Duplicate check (in request)
                if h in seen:
                    entry.update(status="discarded", reason="Duplicate image")
                    results.append(entry)
                    continue
                seen.add(h)

                # 2) Duplicate in DB
                if Cheque.objects.filter(session=self.session, image_hash=h).exists():
                    entry.update(status="discarded", reason="Duplicate image")
                    results.append(entry)
                    continue

                # 3) Validate image format
                try:
                    cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                except:
                    entry.update(status="discarded", reason="Invalid image")
                    results.append(entry)
                    continue

                # 4) OCR → extract amount only
                try:
                    amt, reason_amt = self._extract_and_validate(raw)

                    # If OCR‐parsed amount was invalid (≤ 0), discard immediately
                    if reason_amt:
                        cheque = Cheque(
                            session=self.session,
                            extracted_amt=amt,
                            reason=reason_amt,
                            image_hash=h
                        )
                        cheque.status = "discarded"
                        safe_name = os.path.basename(img.name)
                        cheque.image.save(safe_name, ContentFile(raw))
                        cheque.save()

                        entry.update(
                            amount=float(amt),
                            status="discarded",
                            reason=reason_amt
                        )
                        results.append(entry)
                        continue

                    # 5) Check balance availability
                    if amt > remaining:
                        # Not enough balance: discard with "Insufficient balance"
                        cheque = Cheque(
                            session=self.session,
                            extracted_amt=amt,
                            reason="Insufficient balance",
                            image_hash=h
                        )
                        cheque.status = "discarded"
                        safe_name = os.path.basename(img.name)
                        cheque.image.save(safe_name, ContentFile(raw))
                        cheque.save()

                        entry.update(
                            amount=float(amt),
                            status="discarded",
                            reason="Insufficient balance"
                        )
                        results.append(entry)
                        continue

                    # 6) We have enough balance: accept this cheque
                    cheque = Cheque(
                        session=self.session,
                        extracted_amt=amt,
                        reason="",
                        image_hash=h
                    )
                    cheque.status = "accepted"
                    safe_name = os.path.basename(img.name)
                    cheque.image.save(safe_name, ContentFile(raw))
                    cheque.save()

                    # Deduct from remaining
                    remaining -= amt

                    entry.update(
                        amount=float(amt),
                        status="accepted",
                        reason=""
                    )

                except Exception as e:
                    # Any unexpected error → mark as "error"
                    entry.update(status="error", reason=str(e))
                    traceback.print_exc()

                results.append(entry)

            # ─── Build history and final remaining ─────────────────────────
            history = {
                "accepted": [
                    {"amount": float(c.extracted_amt)}
                    for c in Cheque.objects.filter(session=self.session, status="accepted")
                ],
                "rejected": [
                    {
                      "name":   c.image.name,
                      "reason": c.reason or "Manually discarded"
                    }
                    for c in Cheque.objects.filter(session=self.session, status="discarded")
                ]
            }

            return Response({
                "session_id":       self.session.id,
                "customer_name":    self.session.customer_name,
                "initial_balance":  float(self.session.balance),
                "remaining_balance": float(remaining),
                "history":          history,
                "cheques":          results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": "Internal error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _extract_and_validate(self, raw_bytes):
     img = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
     if img is None:
        return Decimal("0.00"), "Invalid image"

     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
     h, w = gray.shape

    # Lazy-load rupee templates & threshold
     global _RUPEE_TEMPLATES, TM_THRESHOLD
     if "_RUPEE_TEMPLATES" not in globals():
        def _load_template(rel_path):
            try:
                path = os.path.join(settings.BASE_DIR, rel_path)
                return cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            except:
                return None

        _RUPEE_TEMPLATES = [
            _load_template("templates/uco_rupee_label.png"),      # index 0 ⇒ UCO
            _load_template("templates/icici_rupee_label.png"),    # index 1 ⇒ ICICI
            _load_template("templates/rupee_label.png"),          # index 2 ⇒ generic
            _load_template("templates/rupee_label2.png")          # index 3 ⇒ generic
        ]
        TM_THRESHOLD = 0.85

    # ----------------------------------------------------------
    # 1) Try matching all four rupee templates in order
    # ----------------------------------------------------------
     matched_index = None
     match_rect = None  # Will hold (x, y, tmpl_width, tmpl_height)

     for idx, tmpl in enumerate(_RUPEE_TEMPLATES):
        if tmpl is None:
            continue

        res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= TM_THRESHOLD:
            x_t, y_t = max_loc
            t_h, t_w = tmpl.shape  # height, width of the matched template
            match_rect = (x_t, y_t, t_w, t_h)
            matched_index = idx
            break

    # If no template matched, we cannot find the amount ROI
     if match_rect is None:
        return Decimal("0.00"), "Amount region not found"

     x_t, y_t, t_w, t_h = match_rect
     is_uco = (matched_index == 0)

    # ----------------------------------------------------------
    # 2) Compute “amount”-ROI based on which template matched
    # ----------------------------------------------------------
     if is_uco:
        # UCO geometry: narrow box to the right of the “₹.Rs” label
        a_x = max(0, x_t + t_w + 2)
        a_y = max(0, y_t - 12)
        a_w_raw = min(w, a_x + 180)
        a_h_raw = min(h, a_y + 60)
     else:
        # ICICI or any of the generic rupee templates
        a_x = max(0, x_t + 108)
        a_y = max(0, y_t - int(h * 0.008))
        a_w_raw = min(w, a_x + t_w + int(w * 0.15))
        a_h_raw = min(h, a_y + 100)

    # Convert raw bottom coords into width/height
     a_w2 = int(a_w_raw - a_x)
     a_h2 = int(a_h_raw - a_y)

    # ----------------------------------------------------------
    # 3) Draw the amount-ROI in green for debugging
    # ----------------------------------------------------------
     debug_img = img.copy()
     cv2.rectangle(
        debug_img,
        (a_x, a_y),
        (a_x + a_w2, a_y + a_h2),
        color=(0, 255, 0),
        thickness=2
    )

    # Save the debug image
     debug_dir  = os.path.join(settings.BASE_DIR, "debug")
     os.makedirs(debug_dir, exist_ok=True)
     debug_path = os.path.join(debug_dir, f"amount_roi_{uuid.uuid4().hex}.png")
     cv2.imwrite(debug_path, debug_img)
     print(f"Saved AMOUNT-ROI debug image at {debug_path}")

    # ----------------------------------------------------------
    # 4) Crop out exactly that ROI from the original image
    # ----------------------------------------------------------
     a_crop = img[a_y : a_y + a_h2, a_x : a_x + a_w2]

    # ----------------------------------------------------------
    # 5) Binarize & invert (for better OCR on the numerals)
    # ----------------------------------------------------------
     gray_crop = cv2.cvtColor(a_crop, cv2.COLOR_BGR2GRAY)
     _, th = cv2.threshold(
        gray_crop, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
     a_rgb = cv2.cvtColor(th, cv2.COLOR_GRAY2RGB)

    # ----------------------------------------------------------
    # 6) OCR the cropped ROI, parse numeric substrings
    # ----------------------------------------------------------
     try:
        load_models()
        pil        = Image.fromarray(a_rgb)
        pixel_vals = PROCESSOR(pil, return_tensors="pt").pixel_values.to(DEVICE)
        out_ids    = MODEL.generate(pixel_vals, max_length=128)
        txt_amt    = PROCESSOR.batch_decode(out_ids, skip_special_tokens=True)[0]
     except Exception:
        txt_amt = ""

     import re  # still ok to import re here if you want
     amt = Decimal("0.00")
     txt_clean = txt_amt.replace("/", "").replace("-", "").strip()
     found_nums = []
     for m in re.findall(r"[\d,]+(?:\.\d{1,2})?", txt_clean):
        try:
            num = Decimal(m.replace(",", ""))
            found_nums.append(num)
        except:
            pass

     if found_nums:
        amt = max(found_nums)

     if amt <= 0:
        return Decimal("0.00"), "Invalid amount"

     return amt, None


class SessionListView(generics.ListAPIView):
    queryset         = UploadSession.objects.all().order_by("-created_at")
    serializer_class = UploadSessionSerializer


class GeneratePDFView(generics.RetrieveAPIView):
    queryset = UploadSession.objects.all()
    serializer_class = UploadSessionSerializer

    def get(self, request, *args, **kwargs):
        session = self.get_object()
        cheques  = session.cheques.all().order_by("created_at")

        # 1) Build a buffer and SimpleDocTemplate
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        # 2) Define styles (with unique names)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="Heading1Center",
            parent=styles["Heading1"],
            alignment=1,  # 1 = center
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name="Heading2Custom",
            parent=styles["Heading2"],
            spaceAfter=6
        ))
        normal = styles["BodyText"]

        # 3) Build the story (flowables)
        story = []

        # ─── Cover / Title Page ───────────────────────────────────────
        story.append(Paragraph("Cheque Processing Report", styles["Heading1Center"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph(f"Customer: <b>{session.customer_name}</b>", normal))
        story.append(Paragraph(f"Session ID: <b>{session.id}</b>", normal))
        story.append(Paragraph(f"Created At: <b>{session.created_at.strftime('%Y-%m-%d %H:%M:%S')}</b>", normal))
        story.append(Paragraph(f"Initial Balance: <b>₹{session.balance:.2f}</b>", normal))
        story.append(Spacer(1, 0.3 * inch))

        # ─── Accepted Cheques Section ───────────────────────────────────
        accepted_cheques = cheques.filter(status="accepted")
        if accepted_cheques.exists():
            story.append(Paragraph("Accepted Cheques", styles["Heading2Custom"]))
            data = [["#", "Amount (₹)", "Processed At"]]
            for idx, cq in enumerate(accepted_cheques, start=1):
                data.append([
                    str(idx),
                    f"{cq.extracted_amt:.2f}",
                    cq.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ])
            tbl = Table(data, colWidths=[0.5*inch, 1.5*inch, 2.5*inch])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.3 * inch))
        else:
            story.append(Paragraph("<i>No cheques were accepted.</i>", normal))
            story.append(Spacer(1, 0.3 * inch))

        # ─── Discarded Cheques Section ─────────────────────────────────
        discarded_cheques = cheques.filter(status="discarded")
        if discarded_cheques.exists():
            story.append(Paragraph("Discarded Cheques", styles["Heading2Custom"]))
            data = [["#", "Amount (₹)", "Reason", "Processed At"]]
            for idx, cq in enumerate(discarded_cheques, start=1):
                reason = cq.reason or "N/A"
                data.append([
                    str(idx),
                    f"{cq.extracted_amt:.2f}",
                    reason,
                    cq.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ])
            tbl = Table(data, colWidths=[0.5*inch, 1.5*inch, 2.0*inch, 2.0*inch])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.3 * inch))
        else:
            story.append(Paragraph("<i>No cheques were discarded.</i>", normal))
            story.append(Spacer(1, 0.3 * inch))

        # ─── Summary Page ───────────────────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph("Processing Summary", styles["Heading1Center"]))
        story.append(Spacer(1, 0.2 * inch))

        total_accepted_amount = sum([cq.extracted_amt for cq in accepted_cheques], Decimal("0.00"))
        final_balance = session.balance - total_accepted_amount

        summary_data = [
            ["Initial Balance", f"₹{session.balance:.2f}"],
            ["Total Accepted Cheques", str(accepted_cheques.count())],
            ["Sum of Accepted Amounts", f"₹{total_accepted_amount:.2f}"],
            ["Total Discarded Cheques", str(discarded_cheques.count())],
            ["Final Balance", f"₹{final_balance:.2f}"],
        ]
        tbl = Table(summary_data, colWidths=[3.0*inch, 2.0*inch])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.2 * inch))

        # 4) Build the PDF (writes into buf)
        doc.build(story)

        # ─── Save the PDF into session.report_pdf ────────────────────
        buf.seek(0)
        filename = f"report_{session.id}.pdf"
        session.report_pdf.save(
            filename,
            ContentFile(buf.getvalue()),
            save=True
        )

        # 5) Return the URL so frontend can download
        response = HttpResponse(buf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="report_{session.id}.pdf"'
        return response