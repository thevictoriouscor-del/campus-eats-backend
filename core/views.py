import json 
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action 
from rest_framework.views import APIView 
from rest_framework.response import Response
from django.core.mail import send_mail
from django.shortcuts import render 
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import User, Restaurante, Producto, Pedido, DetallePedido
from .serializers import RestauranteSerializer, ProductoSerializer, PedidoSerializer, RegistroSerializer, VerificacionSerializer

# -----------------------------------------------------------------------------
# MAPA DE TARIFAS (Zonas de Dolor)
# -----------------------------------------------------------------------------
TARIFAS_DOMICILIO = {
    # ZONA 1: PLANO / CENTRAL ($2.000)
    'Edificio ML (Mario Laserna)': 2000,
    'Edificio W (Wiesner)': 2000,
    'Edificio SD (Santo Domingo)': 2000,
    'Edificio AU (Aulas)': 2000,
    'Edificio LL (Lleras)': 2000,
    'Edificio B (Ingeniería Vieja)': 2000,
    'Edificio O (Administrativo)': 2000,
    'Edificio RG (Rectoría)': 2000,

    # ZONA 2: SUBIDA / MEDIA ($3.000)
    'Edificio C (Arquitectura)': 3000,
    'Edificio TX (Talleres)': 3000,
    'Edificio G (Sociales)': 3000,
    'Edificio H (Matemáticas)': 3000,
    'Edificio RGA (Pedro Navas)': 3000,
    'Edificio Q (Química)': 3000,
    'Edificio IP (Física)': 3000,
    'Edificio K': 3000,
    'Edificio Ñ': 3000,

    # ZONA 3: EXCURSIÓN / LEJANÍA ($4.000)
    'Centro Deportivo (La Gata)': 4000,
    'Bloque S1 (Arte)': 4000,
    'Edificio Fenicia': 4000,
    'Torre CityU': 4000,
    'Edificio Séneca': 4000,
    'La Caneca': 4000
}
TARIFA_DEFAULT = 3000 # Si ponen un edificio raro, cobramos promedio

# -----------------------------------------------------------------------------
# 0. VISTAS PRINCIPALES (Landing y App)
# -----------------------------------------------------------------------------
def landing_page(request):
    """Muestra la página corporativa de bienvenida"""
    return render(request, 'landing.html')

def webapp(request):
    """Muestra la aplicación funcional (Amarilla)"""
    return render(request, 'index.html')

# -----------------------------------------------------------------------------
# 1. VISTA DE RESTAURANTES
# -----------------------------------------------------------------------------
class RestauranteViewSet(viewsets.ModelViewSet):
    queryset = Restaurante.objects.filter(activo=True)
    serializer_class = RestauranteSerializer
    permission_classes = [permissions.IsAuthenticated]

# -----------------------------------------------------------------------------
# 2. VISTA DE PEDIDOS (Calculadora Inteligente & Logística)
# -----------------------------------------------------------------------------
class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # 1. ADMIN: Ve todo
        if user.is_superuser or user.rol == 'ADMIN':
            return Pedido.objects.all().order_by('-fecha_creacion')
            
        # 2. REPARTIDOR: Ve la "Bolsa" (En cocina sin dueño) + Sus Entregas
        if user.rol == 'REPARTIDOR':
            return Pedido.objects.filter(
                Q(estado='EN_COCINA', repartidor__isnull=True) | # Bolsa disponible
                Q(repartidor=user) # Mis entregas
            ).order_by('-fecha_creacion')
            
        # 3. CLIENTE: Solo ve los suyos
        return Pedido.objects.filter(cliente=user).order_by('-fecha_creacion')

    # --- LÓGICA DE REPARTIDOR (LIMITE 3 PEDIDOS) ---
    @action(detail=True, methods=['post'])
    def tomar_pedido(self, request, pk=None):
        pedido = self.get_object()
        user = request.user
        
        if user.rol != 'REPARTIDOR':
            return Response({'error': 'Solo repartidores pueden tomar pedidos'}, status=403)
            
        if pedido.repartidor is not None:
            return Response({'error': 'Este pedido ya lo tomó alguien más'}, status=400)
            
        # Validar límite de carga (máximo 3 pedidos activos)
        pedidos_activos = Pedido.objects.filter(repartidor=user, estado='EN_CAMINO').count()
        if pedidos_activos >= 3:
            return Response({'error': '¡Tienes 3 pedidos activos! Entrega uno antes de tomar más.'}, status=400)
            
        pedido.repartidor = user
        pedido.estado = 'EN_CAMINO'
        pedido.save()
        return Response({'status': 'Pedido asignado, corre a entregarlo!'}, status=200)

    @action(detail=True, methods=['post'])
    def entregar_pedido(self, request, pk=None):
        pedido = self.get_object()
        if request.user != pedido.repartidor:
            return Response({'error': 'No eres el repartidor de este pedido'}, status=403)
            
        pedido.estado = 'ENTREGADO'
        pedido.save()
        return Response({'status': 'Pedido entregado, buen trabajo!'}, status=200)

    # --- CREACIÓN DE PEDIDO (Calculadora de Costos) ---
    def create(self, request, *args, **kwargs):
        # 1. Parche para leer items desde FormData (cuando hay foto)
        items_raw = request.data.get('items', '[]')
        if isinstance(items_raw, str):
            try:
                items_data = json.loads(items_raw)
            except json.JSONDecodeError:
                items_data = []
        else:
            items_data = items_raw

        # 2. Calcular Tarifa Dinámica según Edificio
        edificio = request.data.get('edificio_entrega', '')
        costo_domicilio_base = TARIFAS_DOMICILIO.get(edificio, TARIFA_DEFAULT)
        
        # --- LÓGICA DE PRIORIDAD ---
        tipo_entrega = request.data.get('tipo_entrega', 'NORMAL')
        costo_extra = 0
        if tipo_entrega == 'PRIORITARIA':
            costo_extra = 2000
        elif tipo_entrega == 'FLEXIBLE':
            costo_extra = -1000
            
        costo_domicilio_total = costo_domicilio_base + costo_extra
        
        # PROCESAR PROPINA
        try:
            propina = int(request.data.get('propina', 0))
        except (ValueError, TypeError):
            propina = 0
        
        total_comida = 0
        productos_validos = []

        # 3. Validar precios de comida (Anti-hackers)
        for item in items_data:
            try:
                prod_db = Producto.objects.get(id=item['id_producto'])
                subtotal = prod_db.precio * int(item['cantidad'])
                total_comida += subtotal
                
                productos_validos.append({
                    'producto': prod_db,
                    'cantidad': int(item['cantidad']),
                    'precio': prod_db.precio
                })
            except Producto.DoesNotExist:
                pass

        total_final = total_comida + costo_domicilio_total + propina

        # 4. Crear el Pedido con los precios corregidos
        # Usamos un diccionario nuevo para forzar nuestros valores calculados
        datos_pedido = request.data.copy()
        datos_pedido['total_pagar'] = total_final
        datos_pedido['costo_domicilio'] = costo_domicilio_total
        datos_pedido['propina'] = propina
        
        serializer = self.get_serializer(data=datos_pedido, partial=True)
        serializer.is_valid(raise_exception=True)
        
        pedido = serializer.save(
            cliente=self.request.user,
            total_pagar=total_final,
            costo_domicilio=costo_domicilio_total,
            propina=propina
        )

        for p in productos_validos:
            DetallePedido.objects.create(
                pedido=pedido,
                producto=p['producto'],
                cantidad=p['cantidad'],
                precio_unitario=p['precio']
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# -----------------------------------------------------------------------------
# VISTAS DE AUTENTICACIÓN (LOGIN, ETC)
# -----------------------------------------------------------------------------
class LoginView(APIView):
    permission_classes = [] 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                # Validar aspirantes pendientes
                if user.rol == 'ASPIRANTE':
                    return Response({"error": "Tu solicitud de domiciliario está en revisión por la administración."}, status=403)
                
                login(request, user)
                # DEVOLVEMOS EL ROL PARA QUE EL FRONTEND SEPA QUÉ PANTALLA MOSTRAR
                return Response({
                    "mensaje": "Bienvenido", 
                    "nombre": user.nombre_completo,
                    "rol": user.rol 
                })
            else:
                return Response({"error": "Cuenta inactiva. Verifica tu correo."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "Credenciales incorrectas"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"mensaje": "Sesión cerrada"})

class RegistroView(APIView):
    permission_classes = [] 
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save() 
            codigo = user.generar_codigo_verificacion()
            
            # --- BLINDAJE DE CORREO (Try-Except) ---
            # Imprimimos en consola por si falla el correo real
            print(f"\n{'='*40}\n📧 INTENTO EMAIL A: {user.email}\n🔑 CÓDIGO DE RESPALDO: {codigo}\n{'='*40}\n")
            
            try:
                # OJO: Cambia el remitente si usas otro correo
                send_mail(
                    'Tu código de verificación - Uniandes Eats',
                    f'Hola {user.nombre_completo}, bienvenido a Uniandes Eats.\n\nTu código es: {codigo}',
                    'contacto@andeseats.com', 
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"❌ ERROR CRÍTICO ENVIANDO CORREO: {e}")
                # No retornamos error al usuario para no bloquear el registro
            
            return Response({"mensaje": "Usuario creado.", "email": user.email}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerificacionView(APIView):
    permission_classes = [] 
    def post(self, request):
        serializer = VerificacionSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            codigo = serializer.validated_data['codigo']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "No existe"}, status=status.HTTP_404_NOT_FOUND)
            if user.codigo_verificacion == codigo:
                user.email_verificado = True
                user.is_active = True
                user.codigo_verificacion = None
                user.save()
                return Response({"mensaje": "Verificado"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Código incorrecto"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)