from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from monedas.services import LimiteService


class Command(BaseCommand):
    help = 'Resetea los límites diarios y mensuales de clientes según corresponda'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-daily',
            action='store_true',
            help='Fuerza el reset diario sin importar la fecha',
        )
        parser.add_argument(
            '--force-monthly',
            action='store_true',
            help='Fuerza el reset mensual sin importar la fecha',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin ejecutar cambios',
        )

    def handle(self, *args, **options):
        hoy = date.today()
        
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando reset de límites - Fecha: {hoy}')
        )

        # Reset diario (siempre se ejecuta, a menos que sea dry-run)
        if options['force_daily'] or not options['dry_run']:
            try:
                if options['dry_run']:
                    # En dry-run, solo contamos los registros que se actualizarían
                    from monedas.models import ConsumoLimiteCliente
                    count = ConsumoLimiteCliente.objects.filter(fecha__lt=hoy).count()
                    self.stdout.write(
                        self.style.WARNING(f'[DRY RUN] Se actualizarían {count} registros de consumo diario')
                    )
                else:
                    count = LimiteService.resetear_consumos_diarios()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Límites diarios reseteados: {count} registros actualizados')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al resetear límites diarios: {str(e)}')
                )

        # Reset mensual (solo si es día 1 del mes o se fuerza)
        if hoy.day == 1 or options['force_monthly']:
            try:
                if options['dry_run']:
                    from monedas.models import ConsumoLimiteCliente
                    count = ConsumoLimiteCliente.objects.all().count()
                    self.stdout.write(
                        self.style.WARNING(f'[DRY RUN] Se resetearían {count} registros de consumo mensual')
                    )
                else:
                    count = LimiteService.resetear_consumos_mensuales()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Límites mensuales reseteados: {count} registros actualizados')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al resetear límites mensuales: {str(e)}')
                )

        # Mostrar estadísticas finales
        if not options['dry_run']:
            try:
                from monedas.models import ConsumoLimiteCliente, LimiteGlobal
                
                # Contar registros activos
                total_consumos = ConsumoLimiteCliente.objects.count()
                consumos_hoy = ConsumoLimiteCliente.objects.filter(fecha=hoy).count()
                limite_vigente = LimiteGlobal.objects.filter(activo=True).first()
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n📊 Estadísticas finales:')
                )
                self.stdout.write(f'   • Total de registros de consumo: {total_consumos}')
                self.stdout.write(f'   • Registros de hoy: {consumos_hoy}')
                if limite_vigente:
                    self.stdout.write(f'   • Límite diario vigente: {limite_vigente.limite_diario:,} PYG')
                    self.stdout.write(f'   • Límite mensual vigente: {limite_vigente.limite_mensual:,} PYG')
                else:
                    self.stdout.write(
                        self.style.WARNING('   • No hay límites globales configurados')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al obtener estadísticas: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Proceso completado - {hoy}')
        )