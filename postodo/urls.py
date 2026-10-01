from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from hardware_store import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Ruta del Frontend
    path('', views.index, name='index'),
    
    # Rutas de Seguridad
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', views.RegisterView.as_view(), name='register'),
    
    # Rutas de la Tienda y el Carro
    path('api/categories/', views.CategoryListView.as_view(), name='category-list'),
    path('api/products/', views.ProductListView.as_view(), name='product-list'),
    path('api/cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('api/checkout/', views.CheckoutView.as_view(), name='checkout'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)