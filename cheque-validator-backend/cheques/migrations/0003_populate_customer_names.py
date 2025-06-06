from django.db import migrations

def populate_names(apps, schema_editor):
    Cheque = apps.get_model('cheques', 'Cheque')
    UploadSession = apps.get_model('cheques', 'UploadSession')
    
    # Get all unique session IDs from cheques
    sessions_with_cheques = Cheque.objects.values_list('session', flat=True).distinct()
    
    # Create a mapping of session IDs to customer names
    session_names = {
        session.id: session.customer_name
        for session in UploadSession.objects.filter(id__in=sessions_with_cheques)
    }
    
    # Update all cheques
    for cheque in Cheque.objects.all():
        cheque.customer_name = session_names.get(cheque.session_id, 'Legacy Customer')
        cheque.save()

class Migration(migrations.Migration):
    dependencies = [
        ('cheques', '0001_initial'),  # Replace with your actual previous migration
    ]

    operations = [
        migrations.RunPython(populate_names),
    ]