from django.db import models
from django.contrib.auth.models import Group

class Roles(Group):
    """
    Modelo que extiende auth.Group para agregar funcionalidad específica de roles
    """
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción detallada del rol")
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name
    
    @property
    def nombre(self):
        """Alias para mantener compatibilidad con código existente"""
        return self.name
