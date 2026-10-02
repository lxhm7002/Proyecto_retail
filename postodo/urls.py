from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from hardware_store import views
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Documentación Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Rutas de Seguridad JWT
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', views.RegisterView.as_view(), name='register'),
    
    # Rutas de la Tienda
    path('api/categories/', views.CategoryListView.as_view(), name='category-list'),
    path('api/products/', views.ProductListView.as_view(), name='product-list'),
    
    # Rutas del Proveedor / Staff
    path('api/products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('api/products/update-stock/', views.ProductUpdateStockView.as_view(), name='product-update-stock'),
    path('api/orders/<int:order_id>/estado/', views.OrderUpdateStatusView.as_view(), name='order-update-status'),
    
    # Rutas del Carro y Checkout Atómico
    path('api/cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('api/checkout/', views.CheckoutView.as_view(), name='checkout'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SOLUCIÓN AL 404: Captura cualquier ruta inexistente y carga el Frontend SPA
urlpatterns += [
    re_path(r'^.*$', views.index, name='catch-all'),
]