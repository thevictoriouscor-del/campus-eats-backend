from django.contrib import admin
from django.utils.html import mark_safe
from django.contrib import messages
from .models import User, Restaurante, Producto, Pedido, DetallePedido

# Configuración General
admin.site.site_header = "Campus Eats Gerencia"
admin.site.site_title = "Admin"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre_completo', 'codigo_estudiante', 'rol', 'is_active')
    search_fields = ('email', 'nombre_completo')
    list_filter = ('rol',)

@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion_local', 'activo')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'restaurante', 'precio', 'disponible')
    list_filter = ('restaurante',)

# --- CONFIGURACIÓN DE PEDIDOS AVANZADA ---
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'jornada_entrega',      # <--- 1. PRIMERO LA HORA (Clave para la ruta)
        'tipo_entrega_visual',  # <--- 2. LUEGO LA PRIORIDAD
        'edificio_entrega',     # <--- 3. LUEGO EL LUGAR
        'cliente_info', 
        'estado_coloreado', 
        'total_formateado', 
        'ver_comprobante', 
        'acciones_rapidas'
    )
    # FILTROS LATERALES PARA GESTIÓN RÁPIDA
    list_filter = ('jornada_entrega', 'tipo_entrega', 'estado', 'fecha_creacion', 'edificio_entrega')
    
    search_fields = ('cliente__nombre_completo', 'cliente__codigo_estudiante', 'id')
    inlines = [DetallePedidoInline]
    
    # ORDEN LÓGICO DE ENTREGA: Hora -> Prioridad (Desc) -> Edificio
    ordering = ['jornada_entrega', '-tipo_entrega', 'edificio_entrega']
    
    # Acciones masivas
    actions = ['marcar_aprobado', 'marcar_en_camino', 'marcar_entregado']

    # 1. Mostrar Info Cliente Bonita
    def cliente_info(self, obj):
        return f"{obj.cliente.nombre_completo} ({obj.cliente.codigo_estudiante})"
    cliente_info.short_description = "Cliente"

    # 2. Dinero con signo pesos
    def total_formateado(self, obj):
        return f"${obj.total_pagar:,.0f}"
    total_formateado.short_description = "Total"

    # 3. Estado con Colores
    def estado_coloreado(self, obj):
        colors = {
            'PENDIENTE': 'orange',
            'VERIFICANDO': 'blue',
            'EN_COCINA': 'purple',
            'EN_CAMINO': 'teal',
            'ENTREGADO': 'green',
            'CANCELADO': 'red',
        }
        color = colors.get(obj.estado, 'black')
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.get_estado_display()}</span>')
    estado_coloreado.short_description = "Estado"

    # 4. PRIORIDAD VISUAL (Iconos)
    def tipo_entrega_visual(self, obj):
        if obj.tipo_entrega == 'PRIORITARIA':
            return mark_safe('<span style="color:red; font-weight:bold;">⚡ FLASH</span>')
        elif obj.tipo_entrega == 'FLEXIBLE':
            return mark_safe('<span style="color:green;">🐢 Relax</span>')
        return "Normal"
    tipo_entrega_visual.short_description = "Prioridad"

    # 5. FOTO CON ZOOM (JavaScript Inyectado)
    def ver_comprobante(self, obj):
        if obj.comprobante_pago:
            img_id = f"img_{obj.id}"
            return mark_safe(f"""
                <img src="{obj.comprobante_pago.url}" 
                     id="{img_id}"
                     width="50" height="50" 
                     style="border-radius: 5px; cursor: zoom-in; object-fit: cover; border: 1px solid #ccc;"
                     onclick="
                        var i = document.getElementById('{img_id}');
                        if(i.style.position === 'fixed') {{
                            i.style.position = 'static';
                            i.style.width = '50px'; i.style.height = '50px';
                            i.style.zIndex = 'auto'; i.style.cursor = 'zoom-in';
                            var overlay = document.getElementById('ov_{img_id}');
                            if(overlay) overlay.remove();
                        }} else {{
                            var d = document.createElement('div');
                            d.id = 'ov_{img_id}';
                            d.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:9998;cursor:zoom-out;';
                            d.onclick = function(){{ i.click(); }};
                            document.body.appendChild(d);
                            i.style.position = 'fixed';
                            i.style.width = 'auto'; i.style.height = '80vh';
                            i.style.top = '50%'; i.style.left = '50%';
                            i.style.transform = 'translate(-50%, -50%)';
                            i.style.zIndex = '9999'; i.style.cursor = 'zoom-out';
                        }}
                     " 
                />
            """)
        return "-"
    ver_comprobante.short_description = "Comprobante"

    # 6. BOTONES DE ACCIÓN RÁPIDA
    def acciones_rapidas(self, obj):
        if obj.estado in ['PENDIENTE', 'VERIFICANDO']:
            return mark_safe(f'<a class="button" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;" href="/admin/core/pedido/{obj.id}/change/">🔍 Revisar</a>')
        return "-"
    acciones_rapidas.short_description = "Acciones"

    # --- FUNCIONES DE ACCIÓN MASIVA (Dropdown) ---
    def marcar_aprobado(self, request, queryset):
        queryset.update(estado='EN_COCINA')
        self.message_user(request, "Pedidos aprobados y enviados a cocina.", messages.SUCCESS)
    marcar_aprobado.short_description = "✅ Aprobar y enviar a Cocina"

    def marcar_en_camino(self, request, queryset):
        queryset.update(estado='EN_CAMINO')
        self.message_user(request, "Pedidos marcados como En Camino.", messages.INFO)
    marcar_en_camino.short_description = "🛵 Marcar como En Camino"

    def marcar_entregado(self, request, queryset):
        queryset.update(estado='ENTREGADO')
        self.message_user(request, "Pedidos finalizados con éxito.", messages.SUCCESS)
    marcar_entregado.short_description = "🏁 Finalizar (Entregado)"