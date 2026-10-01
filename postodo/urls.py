from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from hardware_store import views
from hardware_store.views import (
    CustomTokenObtainPairView, 
    CheckoutView, 
    ProductListView, 
    RegisterView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. RUTA PRINCIPAL (Carga tu interfaz visual index.html)
    path('', views.index, name='index'),

    # 2. RUTAS DE SEGURIDAD (JWT)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='register'),
    
    # 3. RUTAS DE LA TIENDA Y CHECKOUT
    path('api/products/', ProductListView.as_view(), name='product-list'),
    path('api/checkout/', CheckoutView.as_view(), name='checkout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

path('api/cart/', views.CartDetailView.as_view(), name='cart-detail'),