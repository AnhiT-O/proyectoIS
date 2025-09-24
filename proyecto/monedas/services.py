from datetime import date, datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import LimiteGlobal, ConsumoLimiteCliente, Moneda


class LimiteService:
    """
    Servicio para gestionar límites de transacciones de clientes.
    Maneja validación, actualización y consulta de límites diarios y mensuales.
    """

    @staticmethod
    def convertir_a_guaranies(monto, moneda, tipo_transaccion, cliente=None):
        """
        Convierte un monto a guaraníes según el tipo de transacción
        
        Args:
            monto (int): Monto en la moneda original
            moneda (Moneda): Instancia de la moneda
            tipo_transaccion (str): 'COMPRA' o 'VENTA'
            cliente (Cliente): Cliente para aplicar beneficios
            
        Returns:
            int: Monto convertido a guaraníes
        """
        if moneda.simbolo == 'PYG':
            return monto
        
        precios = moneda.get_precios_cliente(cliente)
        
        if tipo_transaccion == 'COMPRA':
            # Cliente compra moneda extranjera, paga en guaraníes
            tasa = precios['precio_venta']
        else:  # VENTA
            # Cliente vende moneda extranjera, recibe guaraníes
            tasa = precios['precio_compra']
        
        return int(monto * tasa)

    @staticmethod
    def obtener_limite_vigente():
        """
        Obtiene el límite global vigente para la fecha actual
        
        Returns:
            LimiteGlobal: Instancia del límite vigente o None si no existe
        """
        return LimiteGlobal.obtener_limite_vigente()

    @staticmethod
    def obtener_o_crear_consumo(cliente, fecha=None):
        """
        Obtiene o crea el registro de consumo para un cliente en una fecha específica
        
        Args:
            cliente (Cliente): Instancia del cliente
            fecha (date): Fecha del consumo, por defecto hoy
            
        Returns:
            ConsumoLimiteCliente: Instancia del consumo
        """
        if fecha is None:
            fecha = date.today()
        
        consumo, created = ConsumoLimiteCliente.objects.get_or_create(
            cliente=cliente,
            fecha=fecha,
            defaults={
                'consumo_diario': 0,
                'consumo_mensual': 0
            }
        )
        
        # Si es un nuevo día, verificar si necesita reset diario
        if created and fecha != date.today():
            consumo.consumo_diario = 0
        
        # Si es un nuevo mes, verificar si necesita reset mensual
        if created and fecha.day == 1:
            consumo.consumo_mensual = 0
            consumo.save()
        
        return consumo

    @staticmethod
    def validar_limite_transaccion(cliente, monto_guaranies):
        """
        Valida si una transacción puede realizarse sin superar los límites
        
        Args:
            cliente (Cliente): Instancia del cliente
            monto_guaranies (int): Monto de la transacción en guaraníes
            
        Returns:
            bool: True si la transacción es válida
            
        Raises:
            ValidationError: Si supera algún límite
        """
        limite = LimiteService.obtener_limite_vigente()
        if not limite:
            raise ValidationError("No hay límites configurados en el sistema")
        
        consumo = LimiteService.obtener_o_crear_consumo(cliente)
        
        # Validar límite diario
        nuevo_consumo_diario = consumo.consumo_diario + monto_guaranies
        if nuevo_consumo_diario > limite.limite_diario:
            disponible_diario = limite.limite_diario - consumo.consumo_diario
            raise ValidationError(
                f"La transacción supera el límite diario. "
                f"Límite: {limite.limite_diario:,} PYG, "
                f"Consumo actual: {consumo.consumo_diario:,} PYG, "
                f"Disponible: {disponible_diario:,} PYG, "
                f"Intentado: {monto_guaranies:,} PYG"
            )
        
        # Validar límite mensual
        nuevo_consumo_mensual = consumo.consumo_mensual + monto_guaranies
        if nuevo_consumo_mensual > limite.limite_mensual:
            disponible_mensual = limite.limite_mensual - consumo.consumo_mensual
            raise ValidationError(
                f"La transacción supera el límite mensual. "
                f"Límite: {limite.limite_mensual:,} PYG, "
                f"Consumo actual: {consumo.consumo_mensual:,} PYG, "
                f"Disponible: {disponible_mensual:,} PYG, "
                f"Intentado: {monto_guaranies:,} PYG"
            )
        
        return True

    @staticmethod
    def obtener_limites_disponibles(cliente):
        """
        Retorna información detallada sobre los límites disponibles para un cliente
        
        Args:
            cliente (Cliente): Instancia del cliente
            
        Returns:
            dict: Información de límites y consumos
        """
        limite = LimiteService.obtener_limite_vigente()
        if not limite:
            return {
                'error': 'No hay límites configurados en el sistema'
            }
        
        consumo = LimiteService.obtener_o_crear_consumo(cliente)
        
        return {
            'limite_diario': limite.limite_diario,
            'limite_mensual': limite.limite_mensual,
            'consumo_diario': consumo.consumo_diario,
            'consumo_mensual': consumo.consumo_mensual,
            'disponible_diario': limite.limite_diario - consumo.consumo_diario,
            'disponible_mensual': limite.limite_mensual - consumo.consumo_mensual,
            'porcentaje_uso_diario': round((consumo.consumo_diario / limite.limite_diario) * 100, 2),
            'porcentaje_uso_mensual': round((consumo.consumo_mensual / limite.limite_mensual) * 100, 2),
        }

    @staticmethod
    @transaction.atomic
    def actualizar_consumo_cliente(cliente, monto_guaranies):
        """
        Actualiza el consumo de un cliente tras una transacción exitosa
        
        Args:
            cliente (Cliente): Instancia del cliente
            monto_guaranies (int): Monto de la transacción en guaraníes
            
        Returns:
            ConsumoLimiteCliente: Instancia actualizada del consumo
        """
        consumo = LimiteService.obtener_o_crear_consumo(cliente)
        consumo.consumo_diario += monto_guaranies
        consumo.consumo_mensual += monto_guaranies
        consumo.save()
        return consumo

    @staticmethod
    def resetear_consumos_diarios():
        """
        Resetea todos los consumos diarios. 
        Usado por el management command para ejecutar diariamente.
        
        Returns:
            int: Número de registros actualizados
        """
        hoy = date.today()
        
        # Obtener todos los consumos de fechas anteriores y actualizarlos
        consumos_anteriores = ConsumoLimiteCliente.objects.filter(fecha__lt=hoy)
        count = consumos_anteriores.count()
        
        # Actualizar fecha y resetear consumo diario
        consumos_anteriores.update(
            fecha=hoy,
            consumo_diario=0
        )
        
        return count

    @staticmethod
    def resetear_consumos_mensuales():
        """
        Resetea todos los consumos mensuales.
        Usado por el management command para ejecutar mensualmente.
        
        Returns:
            int: Número de registros actualizados
        """
        count = ConsumoLimiteCliente.objects.all().update(consumo_mensual=0)
        return count

    @staticmethod
    def validar_y_procesar_transaccion(cliente, moneda, tipo_transaccion, monto_original):
        """
        Método integral que valida límites antes de una transacción y actualiza consumos
        
        Args:
            cliente (Cliente): Instancia del cliente
            moneda (Moneda): Instancia de la moneda
            tipo_transaccion (str): 'COMPRA' o 'VENTA'
            monto_original (int): Monto en la moneda original
            
        Returns:
            dict: Información de la validación y conversión
            
        Raises:
            ValidationError: Si no cumple con los límites
        """
        # Convertir monto a guaraníes
        monto_guaranies = LimiteService.convertir_a_guaranies(
            monto_original, moneda, tipo_transaccion, cliente
        )
        
        # Validar límites
        LimiteService.validar_limite_transaccion(cliente, monto_guaranies)
        
        # Actualizar consumo
        consumo_actualizado = LimiteService.actualizar_consumo_cliente(cliente, monto_guaranies)
        
        # Obtener tasa utilizada
        precios = moneda.get_precios_cliente(cliente)
        tasa = precios['precio_venta'] if tipo_transaccion == 'COMPRA' else precios['precio_compra']
        
        return {
            'monto_original': monto_original,
            'monto_guaranies': monto_guaranies,
            'tasa_utilizada': tasa,
            'consumo_diario_actualizado': consumo_actualizado.consumo_diario,
            'consumo_mensual_actualizado': consumo_actualizado.consumo_mensual,
            'limites_restantes': LimiteService.obtener_limites_disponibles(cliente)
        }