from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <--- Importante para acceder a la configuración
from django.conf.urls.static import static # <--- Importante para servir archivos
from rest_framework.routers import DefaultRouter
from core.views import RestauranteViewSet, PedidoViewSet, RegistroView, VerificacionView, LoginView, LogoutView, home

# El Router crea las direcciones automáticamente (Magia de Django REST)
router = DefaultRouter()
router.register(r'restaurantes', RestauranteViewSet, basename='restaurante')
router.register(r'pedidos', PedidoViewSet, basename='pedido')

urlpatterns = [
    # LA PORTADA DE LA APP (El Frontend Visual)
    path('', home, name='home'),

    # La oficina del jefe (Panel de Admin)
    path('admin/', admin.site.urls),
    
    # API Principal (Restaurantes y Pedidos)
    path('api/', include(router.urls)),
    
    # RUTAS DE AUTENTICACIÓN (Seguridad)
    path('api/auth/registro/', RegistroView.as_view(), name='registro'),
    path('api/auth/verificar/', VerificacionView.as_view(), name='verificar'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
]

# ESTO ES LO NUEVO: Permite ver las fotos subidas en modo desarrollo
# (Solo funciona cuando DEBUG = True en settings.py, o sea, en tu PC)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)