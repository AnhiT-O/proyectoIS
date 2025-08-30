# filepath: /home/josias/Documentos/proyectoIS/proyecto/clientes/scripts/actualizar_beneficios.py

"""
Script para actualizar los beneficios por segmento de todos los clientes existentes.
Ejecutar: python manage.py shell < clientes/scripts/actualizar_beneficios.py
"""

from clientes.models import Cliente

def actualizar_beneficios():
    """Actualiza los beneficios de todos los clientes según su segmento"""
    print("Iniciando actualización de beneficios por segmento...")
    
    clientes = Cliente.objects.all()
    total = clientes.count()
    actualizados = 0
    
    for cliente in clientes:
        # Obtener el beneficio según el segmento
        beneficio = Cliente.BENEFICIOS_SEGMENTO.get(cliente.segmento, 0)
        
        # Actualizar el valor
        if cliente.beneficio_segmento != beneficio:
            cliente.beneficio_segmento = beneficio
            cliente.save(update_fields=['beneficio_segmento'])
            actualizados += 1
    
    print(f"Actualización completada: {actualizados} de {total} clientes actualizados.")

if __name__ == "__main__":
    actualizar_beneficios()