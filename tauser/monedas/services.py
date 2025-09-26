from datetime import date, datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import LimiteGlobal, ConsumoLimiteCliente, Moneda


class LimiteService:
    """
    Servicio centralizado para gestionar límites de transacciones de clientes.
    
    Esta clase proporciona métodos estáticos para validar, actualizar y consultar
    los límites diarios y mensuales que restringen las operaciones de cambio
    de moneda de los clientes según la normativa legal.
    
    Funcionalidades principales:
    - Conversión de montos a guaraníes para control unificado
    - Validación de límites antes de procesar transacciones
    - Actualización de consumos después de transacciones exitosas
    - Consulta de límites disponibles para clientes
    - Reseteo automático de consumos (diario/mensual)
    
    Note:
        Todos los métodos son estáticos ya que no requieren estado de instancia
        y pueden ser llamados directamente desde la clase.
    """

    @staticmethod
    def convertir_a_guaranies(monto, moneda, tipo_transaccion, cliente=None):
        """
        Convierte un monto de cualquier moneda a guaraníes según el tipo de transacción.
        
        Esta función es fundamental para el control de límites ya que permite
        unificar todas las transacciones a una moneda base (guaraníes) independientemente
        de la moneda original de la operación.
        
        Args:
            monto (int): Monto en la moneda original de la transacción
            moneda (Moneda): Instancia de la moneda a convertir
            tipo_transaccion (str): Tipo de operación - 'COMPRA' o 'VENTA'
            cliente (Cliente, optional): Cliente para aplicar beneficios de segmento
            
        Returns:
            int: Monto equivalente en guaraníes
            
        Example:
            # Cliente compra 100 USD
            monto_pyg = LimiteService.convertir_a_guaranies(100, usd, 'COMPRA', cliente)
            # Resultado: 762500 (si precio_venta = 7625)
            
        Note:
            - Para COMPRA: usa precio_venta (lo que paga el cliente)
            - Para VENTA: usa precio_compra (lo que recibe el cliente)
            - Si la moneda ya es PYG, retorna el monto original
        """
        # Si ya está en guaraníes, no necesita conversión
        if moneda.simbolo == 'PYG':
            return monto
        
        # Obtener precios aplicando beneficios del cliente si existe
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
        Obtiene el límite global vigente para la fecha actual.
        
        Método de conveniencia que delega al método del modelo LimiteGlobal
        para obtener la configuración de límites activa en el sistema.
        
        Returns:
            LimiteGlobal: Instancia del límite vigente o None si no hay ninguno configurado
            
        Example:
            limite = LimiteService.obtener_limite_vigente()
            if limite:
                print(f"Límite diario: {limite.limite_diario:,}")
            else:
                print("No hay límites configurados")
        """
        return LimiteGlobal.obtener_limite_vigente()

    @staticmethod
    def obtener_o_crear_consumo(cliente, fecha=None):
        """
        Obtiene o crea el registro de consumo de límites para un cliente en una fecha específica.
        
        Este método es fundamental para el seguimiento de límites ya que asegura que
        siempre exista un registro de consumo para el cliente, creándolo si no existe
        con valores iniciales en cero.
        
        Args:
            cliente (Cliente): Instancia del cliente para el cual obtener/crear el consumo
            fecha (date, optional): Fecha específica del consumo. Defaults to date.today()
            
        Returns:
            ConsumoLimiteCliente: Instancia del registro de consumo (existente o recién creado)
            
        Example:
            # Obtener consumo de hoy para un cliente
            consumo = LimiteService.obtener_o_crear_consumo(cliente)
            
            # Obtener consumo de una fecha específica
            from datetime import date
            consumo = LimiteService.obtener_o_crear_consumo(cliente, date(2024, 1, 15))
            
        Note:
            - Si es un nuevo registro y la fecha no es hoy, resetea el consumo diario
            - Si es primer día del mes, resetea el consumo mensual
            - Usa get_or_create() para evitar condiciones de carrera en concurrencia
        """
        if fecha is None:
            fecha = date.today()
        
        # Obtener o crear el registro de consumo con valores por defecto
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
        Valida si una transacción puede realizarse sin superar los límites establecidos.
        
        Esta función es crítica en el flujo de transacciones ya que previene operaciones
        que excedan los límites diarios o mensuales configurados para evitar
        incumplimientos regulatorios.
        
        Args:
            cliente (Cliente): Instancia del cliente que realizará la transacción
            monto_guaranies (int): Monto de la transacción convertido a guaraníes
            
        Returns:
            bool: True si la transacción puede realizarse sin superar límites
            
        Raises:
            ValidationError: Si no hay límites configurados o si la transacción supera algún límite
            
        Example:
            try:
                LimiteService.validar_limite_transaccion(cliente, 5000000)
                print("Transacción válida")
            except ValidationError as e:
                print(f"Error: {e}")
                
        Note:
            - Verifica tanto el límite diario como el mensual
            - Los mensajes de error incluyen el monto intentado para mayor claridad
            - Debe llamarse ANTES de procesar la transacción real
        """
        # Verificar que existan límites configurados
        limite = LimiteService.obtener_limite_vigente()
        if not limite:
            raise ValidationError("No hay límites configurados en el sistema")
        
        # Obtener el consumo actual del cliente
        consumo = LimiteService.obtener_o_crear_consumo(cliente)
        
        # Validar límite diario
        nuevo_consumo_diario = consumo.consumo_diario + monto_guaranies
        if nuevo_consumo_diario > limite.limite_diario:
            disponible_diario = limite.limite_diario - consumo.consumo_diario
            raise ValidationError(
                f"La transacción supera el límite diario. Se intenta operar con Gs. {monto_guaranies:,}".replace(',', '.')
            )
        
        # Validar límite mensual
        nuevo_consumo_mensual = consumo.consumo_mensual + monto_guaranies
        if nuevo_consumo_mensual > limite.limite_mensual:
            disponible_mensual = limite.limite_mensual - consumo.consumo_mensual
            raise ValidationError(
                f"La transacción supera el límite mensual. Se intenta operar con Gs. {monto_guaranies:,}".replace(',', '.')
            )
        
        return True

    @staticmethod
    def obtener_limites_disponibles(cliente):
        """
        Retorna información detallada sobre los límites disponibles para un cliente.
        
        Proporciona un resumen completo del estado de límites del cliente incluyendo
        límites configurados, consumos actuales, disponibilidades y porcentajes de uso.
        Es útil para mostrar información en interfaces de usuario y validaciones.
        
        Args:
            cliente (Cliente): Instancia del cliente para consultar sus límites
            
        Returns:
            dict: Diccionario con información completa de límites que incluye:
                - limite_diario/limite_mensual: Límites configurados
                - consumo_diario/consumo_mensual: Consumos actuales del cliente  
                - disponible_diario/disponible_mensual: Montos disponibles restantes
                - porcentaje_uso_diario/porcentaje_uso_mensual: % de uso de los límites
                - error: Mensaje si no hay límites configurados
                
        Example:
            limites = LimiteService.obtener_limites_disponibles(cliente)
            if 'error' not in limites:
                print(f"Disponible hoy: Gs. {limites['disponible_diario']:,}")
                print(f"Uso mensual: {limites['porcentaje_uso_mensual']}%")
        """
        # Verificar que existan límites configurados
        limite = LimiteService.obtener_limite_vigente()
        if not limite:
            return {
                'error': 'No hay límites configurados en el sistema'
            }
        
        # Obtener consumo actual del cliente
        consumo = LimiteService.obtener_o_crear_consumo(cliente)
        
        # Calcular disponibilidades y porcentajes de uso
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
        Actualiza el consumo acumulado de un cliente tras una transacción exitosa.
        
        Este método debe llamarse DESPUÉS de que la transacción se haya procesado
        exitosamente para mantener actualizado el registro de consumos del cliente.
        Utiliza transacción atómica para asegurar consistencia de datos.
        
        Args:
            cliente (Cliente): Instancia del cliente que realizó la transacción
            monto_guaranies (int): Monto de la transacción en guaraníes
            
        Returns:
            ConsumoLimiteCliente: Instancia actualizada del registro de consumo
            
        Example:
            # Después de una transacción exitosa
            consumo = LimiteService.actualizar_consumo_cliente(cliente, 5000000)
            print(f"Nuevo consumo diario: Gs. {consumo.consumo_diario:,}")
            
        Note:
            - Incrementa tanto el consumo diario como mensual
            - Usa @transaction.atomic para prevenir inconsistencias
            - Debe llamarse solo después de transacciones exitosas
        """
        consumo = LimiteService.obtener_o_crear_consumo(cliente)
        consumo.consumo_diario += monto_guaranies
        consumo.consumo_mensual += monto_guaranies
        consumo.save()
        return consumo

    @staticmethod
    def resetear_consumos_diarios():
        """
        Resetea todos los consumos diarios para un nuevo día.
        
        Esta función está diseñada para ser ejecutada por un management command
        diariamente (típicamente mediante cron) para resetear los consumos diarios
        de todos los clientes y permitir nuevas operaciones.
        
        Returns:
            int: Número de registros de consumo actualizados
            
        Example:
            # En un management command diario
            registros_actualizados = LimiteService.resetear_consumos_diarios()
            print(f"Resetados {registros_actualizados} consumos diarios")
            
        Note:
            - Solo afecta el consumo_diario, mantiene el consumo_mensual
            - Actualiza la fecha de los registros a hoy
            - Debe ejecutarse una vez por día, idealmente a medianoche
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
        Resetea todos los consumos mensuales para un nuevo mes.
        
        Esta función está diseñada para ser ejecutada por un management command
        mensualmente (típicamente el día 1 de cada mes) para resetear los consumos
        mensuales de todos los clientes.
        
        Returns:
            int: Número de registros de consumo actualizados
            
        Example:
            # En un management command mensual
            registros_actualizados = LimiteService.resetear_consumos_mensuales()
            print(f"Resetados {registros_actualizados} consumos mensuales")
            
        Note:
            - Solo afecta el consumo_mensual, mantiene el consumo_diario
            - Debe ejecutarse el día 1 de cada mes
            - Afecta a todos los clientes del sistema
        """
        count = ConsumoLimiteCliente.objects.all().update(consumo_mensual=0)
        return count

    @staticmethod
    def validar_y_procesar_transaccion(cliente, moneda, tipo_transaccion, monto_original):
        """
        Método integral que valida límites antes de una transacción y actualiza consumos.
        
        Esta es la función más completa del servicio ya que combina validación,
        conversión de moneda y actualización de consumos en una sola operación atómica.
        Está diseñada para ser el punto de entrada principal para procesar transacciones
        con control de límites.
        
        Args:
            cliente (Cliente): Instancia del cliente que realiza la transacción
            moneda (Moneda): Instancia de la moneda de la transacción
            tipo_transaccion (str): Tipo de operación - 'COMPRA' o 'VENTA'
            monto_original (int): Monto en la moneda original de la transacción
            
        Returns:
            dict: Información completa de la transacción procesada que incluye:
                - monto_original: Monto en la moneda original
                - monto_guaranies: Monto convertido a guaraníes
                - tasa_utilizada: Tasa de cambio aplicada
                - consumo_diario_actualizado: Nuevo consumo diario del cliente
                - consumo_mensual_actualizado: Nuevo consumo mensual del cliente
                - limites_restantes: Información de límites disponibles actualizada
                
        Raises:
            ValidationError: Si la transacción supera algún límite configurado
            
        Example:
            try:
                resultado = LimiteService.validar_y_procesar_transaccion(
                    cliente, moneda_usd, 'COMPRA', 100
                )
                print(f"Transacción procesada: Gs. {resultado['monto_guaranies']:,}")
                print(f"Límite diario restante: Gs. {resultado['limites_restantes']['disponible_diario']:,}")
            except ValidationError as e:
                print(f"Transacción rechazada: {e}")
                
        Note:
            - Ejecuta validación ANTES de actualizar consumos
            - Convierte automáticamente montos a guaraníes
            - Actualiza consumos solo si la validación es exitosa
            - Retorna información completa para auditoría y logging
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