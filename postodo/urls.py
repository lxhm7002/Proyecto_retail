from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from hardware_store import views
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', views.RegisterView.as_view(), name='register'), 
    path('api/categories/', views.CategoryListView.as_view(), name='category-list'),
    path('api/products/', views.ProductListView.as_view(), name='product-list'), 
    path('api/products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('api/products/update-stock/', views.ProductUpdateStockView.as_view(), name='product-update-stock'),
    path('api/products/delete/', views.ProductDeleteView.as_view(), name='product-delete'), # NUEVA RUTA
    path('api/orders/<int:order_id>/estado/', views.OrderUpdateStatusView.as_view(), name='order-update-status'),
    path('api/cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('api/checkout/', views.CheckoutView.as_view(), name='checkout'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^.*$', views.index, name='catch-all'),
]