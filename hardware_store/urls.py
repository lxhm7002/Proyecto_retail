from django.urls import path
from .views import CategoryListView, ProductListView, CartDetailView, CheckoutView

urlpatterns = [
    # Catálogo público
    path('categorias/', CategoryListView.as_view(), name='category-list'),
    path('productos/', ProductListView.as_view(), name='product-list'),
    
    # Carro y pagos (Requieren token JWT)
    path('carro/', CartDetailView.as_view(), name='cart-detail'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
]