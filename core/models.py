from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, RegexValidator
import random 

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email: raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('rol', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('correo institucional'), unique=True)
    codigo_estudiante = models.CharField(max_length=9, unique=True, validators=[RegexValidator(regex=r'^\d{9}$', message='El código debe tener exactamente 9 dígitos')])
    nombre_completo = models.CharField(max_length=150)
    celular = models.CharField(max_length=10, blank=True, validators=[RegexValidator(regex=r'^3\d{9}$', message='Debe ser celular válido.')])
    email_verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True)

    class Roles(models.TextChoices):
        ESTUDIANTE = 'ESTUDIANTE', 'Estudiante (Cliente)'
        ASPIRANTE = 'ASPIRANTE', 'Aspirante a Domiciliario' # <--- NUEVO
        REPARTIDOR = 'REPARTIDOR', 'Repartidor Autorizado'
        ADMIN = 'ADMIN', 'Administrador'

    rol = models.CharField(max_length=20, choices=Roles.choices, default=Roles.ESTUDIANTE)
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['codigo_estudiante', 'nombre_completo']
    
    def generar_codigo_verificacion(self):
        codigo = str(random.randint(100000, 999999))
        self.codigo_verificacion = codigo
        self.save()
        return codigo
    def __str__(self): return f"{self.nombre_completo} ({self.rol})"

class Restaurante(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion_local = models.CharField(max_length=100)
    celular_pedidos = models.CharField(max_length=10)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.nombre

class Producto(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=0) 
    disponible = models.BooleanField(default=True)
    def __str__(self): return f"{self.nombre} - ${self.precio}"

class Pedido(models.Model):
    class Estados(models.TextChoices):
        PENDIENTE_PAGO = 'PENDIENTE', 'Pendiente de Pago'
        VERIFICANDO = 'VERIFICANDO', 'Verificando Transferencia'
        EN_COCINA = 'EN_COCINA', 'Aprobado - En Cocina'
        EN_CAMINO = 'EN_CAMINO', 'En Camino'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    class Jornadas(models.TextChoices):
        TURNO_1 = '12:00 - 12:45', 'Almuerzo Temprano (12:00 - 12:45)'
        TURNO_2 = '12:45 - 13:30', 'Almuerzo Pico (12:45 - 1:30)'
        TURNO_3 = '13:30 - 14:15', 'Almuerzo Tarde (1:30 - 2:15)'

    class Prioridad(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        PRIORITARIA = 'PRIORITARIA', '⚡ Flash (+$2.000)'
        FLEXIBLE = 'FLEXIBLE', '🐢 Relax (-$1.000)'

    cliente = models.ForeignKey(User, on_delete=models.PROTECT, related_name='pedidos')
    repartidor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='entregas_asignadas')
    
    edificio_entrega = models.CharField(max_length=50)
    detalle_ubicacion = models.CharField(max_length=100)
    jornada_entrega = models.CharField(max_length=20, choices=Jornadas.choices, default=Jornadas.TURNO_2)
    tipo_entrega = models.CharField(max_length=20, choices=Prioridad.choices, default=Prioridad.NORMAL)
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.PENDIENTE_PAGO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # DINERO
    total_pagar = models.DecimalField(max_digits=10, decimal_places=0)
    costo_domicilio = models.DecimalField(max_digits=10, decimal_places=0, default=2000)
    propina = models.DecimalField(max_digits=10, decimal_places=0, default=0) # <--- CON PROPINA
    
    comprobante_pago = models.ImageField(upload_to='comprobantes/', blank=True, null=True)

    def __str__(self): return f"Pedido #{self.id} - {self.cliente.nombre_completo}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    def save(self, *args, **kwargs):
        if not self.precio_unitario: self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)
    def subtotal(self): return self.cantidad * self.precio_unitario if self.precio_unitario else 0
    def __str__(self): return f"{self.cantidad}x {self.producto.nombre}"