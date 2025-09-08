from django.db import migrations

def crear_segmentaciones_default(apps, schema_editor):
    SegmentacionCliente = apps.get_model('clientes', 'SegmentacionCliente')
    
    # Crear segmentaciones si no existen
    segmentaciones = [
        {'nombre': 'Minorista', 'porcentaje_beneficio': 0},
        {'nombre': 'Corporativo', 'porcentaje_beneficio': 5},
        {'nombre': 'VIP', 'porcentaje_beneficio': 10},
    ]
    
    for seg in segmentaciones:
        SegmentacionCliente.objects.get_or_create(
            nombre=seg['nombre'],
            defaults={'porcentaje_beneficio': seg['porcentaje_beneficio']}
        )

def revertir_segmentaciones(apps, schema_editor):
    SegmentacionCliente = apps.get_model('clientes', 'SegmentacionCliente')
    SegmentacionCliente.objects.filter(
        nombre__in=['Minorista', 'Corporativo', 'VIP']
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('clientes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(crear_segmentaciones_default, revertir_segmentaciones),
    ]
