from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Restaurante, Producto, Pedido, DetallePedido

# -----------------------------------------------------------------------------
# 1. TRADUCTOR DE USUARIOS
# -----------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nombre_completo', 'codigo_estudiante', 'rol']

# -----------------------------------------------------------------------------
# 2. TRADUCTOR DE PRODUCTOS
# -----------------------------------------------------------------------------
class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'disponible', 'restaurante']

# -----------------------------------------------------------------------------
# 3. TRADUCTOR DE RESTAURANTES
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
# 5. TRADUCTOR DE PEDIDOS (CON JORNADA Y PRIORIDAD)
# -----------------------------------------------------------------------------
class PedidoSerializer(serializers.ModelSerializer):
    items = DetallePedidoSerializer(many=True, read_only=True)
    cliente_info = UserSerializer(source='cliente', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'cliente_info', 'edificio_entrega', 'detalle_ubicacion', 
            'estado', 'total_pagar', 'costo_domicilio', 
            'comprobante_pago', 'fecha_creacion', 'items',
            'jornada_entrega', 'tipo_entrega'  # <--- NUEVOS CAMPOS AGREGADOS
        ]
        extra_kwargs = {'cliente': {'read_only': True}}

# -----------------------------------------------------------------------------
# 6. REGISTRO Y VERIFICACIÓN
# -----------------------------------------------------------------------------
class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ['email', 'codigo_estudiante', 'nombre_completo', 'celular', 'password', 'rol']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            codigo_estudiante=validated_data['codigo_estudiante'],
            nombre_completo=validated_data['nombre_completo'],
            celular=validated_data.get('celular', ''),
            rol=validated_data.get('rol', 'ESTUDIANTE'),
            is_active=False
        )
        return user

class VerificacionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=6)