from django.shortcuts import render
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import CustomTokenObtainPairSerializer, CategorySerializer, ProductSerializer, CartSerializer

User = get_user_model()

# =========================================================
# VISTA PRINCIPAL (FRONTEND SPA)
# =========================================================
def index(request):
    return render(request, 'index.html')

# =========================================================
# GESTIÓN DE CATÁLOGO Y FILTROS (django-filter)
# =========================================================
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    # Integración de filtros obligatorios
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category'] 
    search_fields = ['name', 'brand']

# =========================================================
# GESTIÓN DE PROVEEDORES / STAFF
# =========================================================
class ProductCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Acceso denegado. Solo proveedores pueden agregar productos."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"mensaje": "Producto creado con éxito"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductUpdateStockView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Acceso denegado."}, status=status.HTTP_403_FORBIDDEN)
        
        product_id = request.data.get('product_id')
        cantidad_a_sumar = request.data.get('stock')
        
        try:
            product = Product.objects.get(id=product_id)
            product.stock += int(cantidad_a_sumar)
            product.save()
            return Response({"mensaje": "Stock actualizado con éxito"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

# =========================================================
# ACTUALIZACIÓN DE ESTADOS DE ORDEN Y DEVOLUCIÓN DE STOCK
# =========================================================
class OrderUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, order_id):
        if not request.user.is_staff:
            return Response({"error": "Acceso denegado."}, status=status.HTTP_403_FORBIDDEN)
            
        new_status = request.data.get('status')
        try:
            with transaction.atomic():
                order = Order.objects.get(id=order_id)
                
                # Si el administrador CANCELA, el stock vuelve al catálogo automáticamente
                if new_status == 'CANCELADO' and order.status != 'CANCELADO':
                    items = OrderItem.objects.filter(order=order)
                    for item in items:
                        item.product.stock += item.quantity
                        item.product.save()
                
                order.status = new_status
                order.save()
                return Response({"mensaje": f"Orden actualizada a {new_status}"}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Orden no encontrada"}, status=status.HTTP_404_NOT_FOUND)

# =========================================================
# FLUJO DEL CARRO Y TRANSACCIÓN ATÓMICA
# =========================================================
class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)
    
    def post(self, request):
        product_id = request.data.get('product_id') or request.data.get('id')
        try:
            product = Product.objects.get(id=product_id)
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
            
            if cart_item.quantity + 1 > product.stock:
                return Response({"error": f"No puedes agregar más. Solo hay {product.stock} en stock."}, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity += 1
            cart_item.save()
            return Response(CartSerializer(cart).data)
        except Product.DoesNotExist:
            return Response({"error": "El producto no existe en la BD."}, status=status.HTTP_404_NOT_FOUND)
            
    def delete(self, request):
        product_id = request.data.get('product_id')
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            return Response(CartSerializer(cart).data)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({"error": "El producto no está en el carro."}, status=status.HTTP_404_NOT_FOUND)

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            with transaction.atomic():
                cart = Cart.objects.get(user=request.user)
                items = CartItem.objects.filter(cart=cart)
                
                if not items.exists():
                    return Response({"error": "El carro está vacío"}, status=status.HTTP_400_BAD_REQUEST)
                
                order = Order.objects.create(user=request.user)
                total = 0
                
                for item in items:
                    if item.product.stock < item.quantity:
                        raise ValueError(f"Stock insuficiente para {item.product.name}.")
                    
                    # Descuento atómico del inventario
                    item.product.stock -= item.quantity
                    item.product.save()
                    
                    OrderItem.objects.create(
                        order=order, 
                        product=item.product, 
                        quantity=item.quantity,
                        historical_price=item.product.price
                    )
                    total += item.product.price * item.quantity
                    
                order.total_amount = total
                order.status = 'PAGADO'
                order.save()
                
                items.delete()
                
                return Response({"mensaje": "Compra realizada con éxito", "orden_id": order.id}, status=status.HTTP_201_CREATED)
                
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Falla en BD: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =========================================================
# AUTENTICACIÓN JWT Y REGISTRO
# =========================================================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response({"error": "Por favor ingresa un usuario y contraseña."}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=username).exists():
                return Response({"error": f"El usuario '{username}' ya está registrado."}, status=status.HTTP_400_BAD_REQUEST)
            
            User.objects.create_user(username=username, password=password)
            return Response({"message": "Usuario registrado con éxito"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Error interno en BD: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)