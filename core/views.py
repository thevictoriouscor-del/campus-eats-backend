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
# MAPA DE TARIFAS
# -----------------------------------------------------------------------------
TARIFAS_DOMICILIO = {
    'Edificio ML (Mario Laserna)': 2000, 'Edificio W (Wiesner)': 2000, 'Edificio SD (Santo Domingo)': 2000,
    'Edificio AU (Aulas)': 2000, 'Edificio LL (Lleras)': 2000, 'Edificio B (Ingeniería Vieja)': 2000,
    'Edificio O (Administrativo)': 2000, 'Edificio RG (Rectoría)': 2000,
    'Edificio C (Arquitectura)': 3000, 'Edificio TX (Talleres)': 3000, 'Edificio G (Sociales)': 3000,
    'Edificio H (Matemáticas)': 3000, 'Edificio RGA (Pedro Navas)': 3000, 'Edificio Q (Química)': 3000,
    'Edificio IP (Física)': 3000, 'Edificio K': 3000, 'Edificio Ñ': 3000,
    'Centro Deportivo (La Gata)': 4000, 'Bloque S1 (Arte)': 4000, 'Edificio Fenicia': 4000,
    'Torre CityU': 4000, 'Edificio Séneca': 4000, 'La Caneca': 4000
}
TARIFA_DEFAULT = 3000

# -----------------------------------------------------------------------------
# VISTAS PRINCIPALES
# -----------------------------------------------------------------------------
def landing_page(request): return render(request, 'landing.html')
def webapp(request): return render(request, 'index.html')

class RestauranteViewSet(viewsets.ModelViewSet):
    queryset = Restaurante.objects.filter(activo=True)
    serializer_class = RestauranteSerializer
    permission_classes = [permissions.IsAuthenticated]

class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.rol == 'ADMIN': return Pedido.objects.all().order_by('-fecha_creacion')
        if user.rol == 'REPARTIDOR': return Pedido.objects.filter(Q(estado='EN_COCINA', repartidor__isnull=True) | Q(repartidor=user)).order_by('-fecha_creacion')
        return Pedido.objects.filter(cliente=user).order_by('-fecha_creacion')

    @action(detail=True, methods=['post'])
    def tomar_pedido(self, request, pk=None):
        pedido = self.get_object()
        user = request.user
        if user.rol != 'REPARTIDOR': return Response({'error': 'No autorizado'}, 403)
        if pedido.repartidor: return Response({'error': 'Ya tomado'}, 400)
        pedidos_activos = Pedido.objects.filter(repartidor=user, estado='EN_CAMINO').count()
        if pedidos_activos >= 3: return Response({'error': '¡Límite de 3 pedidos activos!'}, 400)
        pedido.repartidor = user; pedido.estado = 'EN_CAMINO'; pedido.save()
        return Response({'status': 'Asignado'}, 200)

    @action(detail=True, methods=['post'])
    def entregar_pedido(self, request, pk=None):
        pedido = self.get_object()
        if request.user != pedido.repartidor: return Response({'error': 'No es tuyo'}, 403)
        pedido.estado = 'ENTREGADO'; pedido.save()
        return Response({'status': 'Entregado'}, 200)

    def create(self, request, *args, **kwargs):
        try:
            items_raw = request.data.get('items', '[]')
            items_data = json.loads(items_raw) if isinstance(items_raw, str) else items_raw
            edificio = request.data.get('edificio_entrega', '')
            costo_domicilio_base = TARIFAS_DOMICILIO.get(edificio, TARIFA_DEFAULT)
            tipo_entrega = request.data.get('tipo_entrega', 'NORMAL')
            costo_extra = 2000 if tipo_entrega == 'PRIORITARIA' else (-1000 if tipo_entrega == 'FLEXIBLE' else 0)
            
            try: propina = int(request.data.get('propina', 0))
            except: propina = 0
            
            costo_domicilio_total = costo_domicilio_base + costo_extra
            total_comida = 0
            productos_validos = []
            for item in items_data:
                try:
                    prod_db = Producto.objects.get(id=item['id_producto'])
                    subtotal = prod_db.precio * int(item['cantidad'])
                    total_comida += subtotal
                    productos_validos.append({'producto': prod_db, 'cantidad': int(item['cantidad']), 'precio': prod_db.precio})
                except Producto.DoesNotExist: pass
            
            total_final = total_comida + costo_domicilio_total + propina
            datos_pedido = request.data.copy()
            datos_pedido['total_pagar'] = total_final
            datos_pedido['costo_domicilio'] = costo_domicilio_total
            datos_pedido['propina'] = propina
            
            serializer = self.get_serializer(data=datos_pedido, partial=True)
            serializer.is_valid(raise_exception=True)
            pedido = serializer.save(cliente=self.request.user, total_pagar=total_final, costo_domicilio=costo_domicilio_total, propina=propina)

            for p in productos_validos:
                DetallePedido.objects.create(pedido=pedido, producto=p['producto'], cantidad=p['cantidad'], precio_unitario=p['precio'])

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class LoginView(APIView):
    permission_classes = [] 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            if user.is_active:
                if user.rol == 'ASPIRANTE': return Response({"error": "Tu solicitud está en revisión."}, 403)
                login(request, user)
                return Response({"mensaje": "Bienvenido", "nombre": user.nombre_completo, "rol": user.rol})
            return Response({"error": "Cuenta inactiva"}, 401)
        return Response({"error": "Credenciales incorrectas"}, 400)

class LogoutView(APIView):
    def post(self, request): logout(request); return Response({"mensaje": "Bye"})

class RegistroView(APIView):
    permission_classes = [] 
    def post(self, request):
        try:
            serializer = RegistroSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                codigo = user.generar_codigo_verificacion()
                
                print(f"\n{'='*40}\n📧 CÓDIGO RESPALDO: {codigo}\n{'='*40}\n")
                
                # BLINDAJE DE CORREO
                try:
                    send_mail(
                        'Tu código de verificación - Uniandes Eats',
                        f'Hola {user.nombre_completo}, bienvenido.\n\nTu código es: {codigo}',
                        'contacto@andeseats.com', 
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"❌ ERROR CORREO (Pero continuamos): {e}")
                
                return Response({"mensaje": "Usuario creado.", "email": user.email}, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Captura errores generales para no dar 500 HTML
            print(f"❌ ERROR GENERAL REGISTRO: {e}")
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class VerificacionView(APIView):
    permission_classes = [] 
    def post(self, request):
        serializer = VerificacionSerializer(data=request.data)
        if serializer.is_valid():
            try: user = User.objects.get(email=serializer.validated_data['email'])
            except: return Response({"error": "No existe"}, 404)
            if user.codigo_verificacion == serializer.validated_data['codigo']:
                user.email_verificado=True; user.is_active=True; user.save(); return Response({"Ok":1})
            return Response({"error": "Código incorrecto"}, 400)
        return Response(serializer.errors, 400)