from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from core.views import RestauranteViewSet, PedidoViewSet, RegistroView, VerificacionView, LoginView, LogoutView, landing_page, webapp

router = DefaultRouter()
router.register(r'restaurantes', RestauranteViewSet, basename='restaurante')
router.register(r'pedidos', PedidoViewSet, basename='pedido')

urlpatterns = [
    # 1. LA PORTADA CORPORATIVA (Raíz)
    path('', landing_page, name='landing'),

    # 2. LA APP FUNCIONAL (Ahora en /app/)
    path('app/', webapp, name='webapp'),

    # Panel Admin
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include(router.urls)),
    path('api/auth/registro/', RegistroView.as_view(), name='registro'),
    path('api/auth/verificar/', VerificacionView.as_view(), name='verificar'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)