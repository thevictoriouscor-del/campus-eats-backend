from django.contrib import admin
from django.utils.html import mark_safe
from django.contrib import messages
from .models import User, Restaurante, Producto, Pedido, DetallePedido

# -----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL DEL PANEL
# -----------------------------------------------------------------------------
admin.site.site_header = "Andes Eats Gerencia"
admin.site.site_title = "Admin"
admin.site.index_title = "Panel de Control"

# -----------------------------------------------------------------------------
# 1. USUARIOS
# -----------------------------------------------------------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre_completo', 'codigo_estudiante', 'rol_visual', 'is_active', 'email_verificado')
    search_fields = ('email', 'nombre_completo', 'codigo_estudiante')
    list_filter = ('rol', 'is_active')
    actions = ['activar_usuarios', 'convertir_repartidor']

    def rol_visual(self, obj):
        colors = {
            'ESTUDIANTE': 'blue',
            'ASPIRANTE': 'orange',
            'REPARTIDOR': 'purple',
            'ADMIN': 'red',
        }
        color = colors.get(obj.rol, 'black')
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.get_rol_display()}</span>')
    rol_visual.short_description = "Rol"

    # Acciones masivas para gestión de personal
    def activar_usuarios(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Usuarios activados exitosamente.", messages.SUCCESS)
    activar_usuarios.short_description = "✅ Activar usuarios seleccionados"

    def convertir_repartidor(self, request, queryset):
        queryset.update(rol='REPARTIDOR', is_active=True)
        self.message_user(request, "Usuarios ascendidos a Repartidores.", messages.SUCCESS)
    convertir_repartidor.short_description = "🛵 Aprobar como Repartidor"

# -----------------------------------------------------------------------------
# 2. RESTAURANTES
# -----------------------------------------------------------------------------
@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion_local', 'celular_pedidos', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

# -----------------------------------------------------------------------------
# 3. PRODUCTOS
# -----------------------------------------------------------------------------
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'restaurante', 'precio_formato', 'disponible')
    list_filter = ('restaurante', 'disponible')
    search_fields = ('nombre',)

    def precio_formato(self, obj):
        return f"${obj.precio:,.0f}"
    precio_formato.short_description = "Precio"

# -----------------------------------------------------------------------------
# 4. PEDIDOS (LA JOYA DE LA CORONA)
# -----------------------------------------------------------------------------
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('subtotal_visual',)

    def subtotal_visual(self, obj):
        return f"${obj.subtotal():,.0f}"
    subtotal_visual.short_description = "Subtotal"

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista
    list_display = (
        'id', 
        'jornada_entrega',      # Logística: Hora
        'tipo_entrega_visual',  # Logística: Prioridad
        'edificio_entrega',     # Logística: Lugar
        'estado_coloreado',     # Estado actual
        'cliente_info',         # Quién pide
        'repartidor_info',      # Quién lleva (Nuevo)
        'total_final_visual',   # Cuánto cobramos
        'ver_comprobante',      # Foto del pago
        'acciones_rapidas'      # Botones
    )
    
    # Filtros laterales para Sara
    list_filter = (
        'jornada_entrega', 
        'tipo_entrega', 
        'estado', 
        'edificio_entrega',
        'fecha_creacion'
    )
    
    search_fields = ('cliente__nombre_completo', 'cliente__codigo_estudiante', 'id', 'edificio_entrega')
    
    # Orden por defecto: Primero la Jornada, luego Prioridad, luego Edificio
    ordering = ['jornada_entrega', '-tipo_entrega', 'edificio_entrega']
    
    inlines = [DetallePedidoInline]
    
    actions = ['marcar_aprobado', 'marcar_en_camino', 'marcar_entregado']

    # --- MÉTODOS VISUALES ---

    def cliente_info(self, obj):
        return f"{obj.cliente.nombre_completo}"
    cliente_info.short_description = "Cliente"

    def repartidor_info(self, obj):
        if obj.repartidor:
            return f"🛵 {obj.repartidor.nombre_completo}"
        return "-"
    repartidor_info.short_description = "Repartidor"

    def total_final_visual(self, obj):
        # Muestra el total con propina si aplica
        return f"${obj.total_pagar:,.0f}"
    total_final_visual.short_description = "Total"

    def estado_coloreado(self, obj):
        colors = {
            'PENDIENTE': 'orange',
            'VERIFICANDO': 'blue',
            'EN_COCINA': 'purple', # Aprobado
            'EN_CAMINO': 'teal',
            'ENTREGADO': 'green',
            'CANCELADO': 'red',
        }
        color = colors.get(obj.estado, 'black')
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.get_estado_display()}</span>')
    estado_coloreado.short_description = "Estado"

    def tipo_entrega_visual(self, obj):
        if obj.tipo_entrega == 'PRIORITARIA':
            return mark_safe('<span style="color:red; font-weight:900;">⚡ FLASH</span>')
        elif obj.tipo_entrega == 'FLEXIBLE':
            return mark_safe('<span style="color:green;">🐢 Relax</span>')
        return "Normal"
    tipo_entrega_visual.short_description = "Prioridad"

    # FOTO CON ZOOM (JavaScript Inyectado)
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

    # BOTONES DE ACCIÓN RÁPIDA
    def acciones_rapidas(self, obj):
        if obj.estado in ['PENDIENTE', 'VERIFICANDO']:
            return mark_safe(f'''
                <a class="button" style="background-color: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-weight:bold; text-decoration: none;" href="/admin/core/pedido/{obj.id}/change/">
                   🔍 Revisar
                </a>
            ''')
        return "-"
    acciones_rapidas.short_description = "Acciones"

    # --- FUNCIONES DE ACCIÓN MASIVA (Dropdown) ---
    def marcar_aprobado(self, request, queryset):
        queryset.update(estado='EN_COCINA')
        self.message_user(request, "✅ Pedidos aprobados y enviados a cocina.", messages.SUCCESS)
    marcar_aprobado.short_description = "✅ Aprobar y enviar a Cocina"

    def marcar_en_camino(self, request, queryset):
        queryset.update(estado='EN_CAMINO')
        self.message_user(request, "🛵 Pedidos marcados como En Camino.", messages.INFO)
    marcar_en_camino.short_description = "🛵 Marcar como En Camino"

    def marcar_entregado(self, request, queryset):
        queryset.update(estado='ENTREGADO')
        self.message_user(request, "🏁 Pedidos finalizados con éxito.", messages.SUCCESS)
    marcar_entregado.short_description = "🏁 Finalizar (Entregado)"