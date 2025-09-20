# Variable global para el stock de guaraníes
# Puedes modificar el valor inicial según el stock real del sistema

STOCK_GUARANIES = 10000000  # Ejemplo: 10 millones de guaraníes disponibles

# Puedes importar esta variable en cualquier módulo:
# from monedas.guaranies import STOCK_GUARANIES

def puede_vender_divisa(monto_guaranies):
    """
    Verifica si hay suficiente stock de guaraníes para realizar la venta de divisas.
    Retorna True si hay suficiente, False si no.
    """
    global STOCK_GUARANIES
    return monto_guaranies <= STOCK_GUARANIES

def actualizar_stock_guaranies(monto):
    """
    Actualiza el stock de guaraníes después de una transacción.
    Usar monto positivo para sumar (compra de divisa), negativo para restar (venta de divisa).
    """
    global STOCK_GUARANIES
    STOCK_GUARANIES += monto
    return STOCK_GUARANIES

def obtener_stock_guaranies():
    """
    Retorna el stock actual de guaraníes.
    """
    global STOCK_GUARANIES
    return STOCK_GUARANIES

# Ejemplo de uso:
# if puede_vender_divisa(monto_a_entregar):
#     # Realizar la venta
# else:
#     # Mostrar mensaje de stock insuficiente
