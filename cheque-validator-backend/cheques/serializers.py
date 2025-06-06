# serializers.py

from rest_framework import serializers
from .models import UploadSession, Cheque
from django.core.validators import FileExtensionValidator

class ChequeSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='session.customer_name', read_only=True)

    class Meta:
        model = Cheque
        fields = [
            'id',
            'customer_name',
            'image',
            'extracted_amt',
            'status',
            'reason'
        ]
        read_only_fields = fields


class UploadSessionSerializer(serializers.ModelSerializer):
    # The incoming “cheques” list of ImageFiles (only on create)
    cheques = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
        ),
        write_only=True,
        help_text="Upload one or more cheque images"
    )

    balance = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Nested read‐only representation of processed Cheque objects
    processed_cheques = ChequeSerializer(
        source='cheques',
        many=True,
        read_only=True
    )

    # Expose the PDF download URL
    report_pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UploadSession
        fields = [
            'id',
            'customer_name',
            'balance',
            'cheques',             # write‐only on create
            'processed_cheques',   # read‐only list of Cheques
            'report_pdf_url',      # <-- we must include this, otherwise DRF will complain
            'created_at'
        ]
        read_only_fields = [
            'id',
            'processed_cheques',
            'report_pdf_url',
            'created_at'
        ]

    def get_report_pdf_url(self, obj):
        request = self.context.get('request')
        if obj.report_pdf:
            # Build absolute URL if a request context is available,
            # otherwise return the relative media URL.
            if request is not None:
                return request.build_absolute_uri(obj.report_pdf.url)
            return obj.report_pdf.url
        return None

    def create(self, validated_data):
        images = validated_data.pop('cheques')
        session = UploadSession.objects.create(**validated_data)
        self.context['session'] = session
        return session
