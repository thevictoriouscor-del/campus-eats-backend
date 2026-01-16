from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Restaurante, Producto, Pedido, DetallePedido

# -----------------------------------------------------------------------------
# 1. TRADUCTOR DE USUARIOS
# -----------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Agregamos 'celular' y 'rol' para que la App sepa quién es quién
        fields = ['id', 'nombre_completo', 'codigo_estudiante', 'rol', 'celular']

# -----------------------------------------------------------------------------
# 2. PRODUCTOS
# -----------------------------------------------------------------------------
class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'disponible', 'restaurante']

# -----------------------------------------------------------------------------
# 3. RESTAURANTES
# -----------------------------------------------------------------------------
class RestauranteSerializer(serializers.ModelSerializer):
    productos = ProductoSerializer(many=True, read_only=True)
    class Meta:
        model = Restaurante
        fields = ['id', 'nombre', 'ubicacion_local', 'celular_pedidos', 'activo', 'productos']

# -----------------------------------------------------------------------------
# 4. DETALLE DE PEDIDO
# -----------------------------------------------------------------------------
class DetallePedidoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(source='producto.nombre', read_only=True)
    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal']

# -----------------------------------------------------------------------------
# 5. PEDIDOS (COMPLETO CON DOMICILIARIO, PROPINA Y FOTOS)
# -----------------------------------------------------------------------------
class PedidoSerializer(serializers.ModelSerializer):
    items = DetallePedidoSerializer(many=True, read_only=True)
    cliente_info = UserSerializer(source='cliente', read_only=True)
    repartidor_info = UserSerializer(source='repartidor', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'cliente_info', 'repartidor', 'repartidor_info',
            'edificio_entrega', 'detalle_ubicacion', 
            'estado', 'total_pagar', 'costo_domicilio', 'propina', # <--- CON PROPINA
            'comprobante_pago', 'fecha_creacion', 'items',
            'jornada_entrega', 'tipo_entrega' # <--- JORNADAS Y PRIORIDAD
        ]
        # Estos campos los llena el sistema automáticamente, no el usuario
        extra_kwargs = {'cliente': {'read_only': True}, 'repartidor': {'read_only': True}}

# -----------------------------------------------------------------------------
# 6. REGISTRO (CON REGLAS DE NEGOCIO)
# -----------------------------------------------------------------------------
class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    # Campo opcional para solicitar ser repartidor
    es_aspirante = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = ['email', 'codigo_estudiante', 'nombre_completo', 'celular', 'password', 'rol', 'es_aspirante']
        extra_kwargs = {'rol': {'read_only': True}} # El rol se asigna internamente
    
    def create(self, validated_data):
        es_aspirante = validated_data.pop('es_aspirante', False)
        
        # Lógica de asignación de Rol
        if es_aspirante:
            rol_asignado = 'ASPIRANTE'
        else:
            rol_asignado = 'ESTUDIANTE' # Por defecto (Aquí caerían también los profes por ahora)
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            codigo_estudiante=validated_data['codigo_estudiante'],
            nombre_completo=validated_data['nombre_completo'],
            celular=validated_data.get('celular', ''),
            rol=rol_asignado,
            # IMPORTANTE: Nace ACTIVO para que pueda entrar a ver el menú de una vez
            # El bloqueo de pedidos por no verificación se hace en views.py
            is_active=True 
        )
        return user

class VerificacionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=6)