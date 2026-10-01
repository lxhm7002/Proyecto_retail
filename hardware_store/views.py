from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import CustomTokenObtainPairSerializer, CategorySerializer, ProductSerializer, CartSerializer
from django.shortcuts import render
from rest_framework.generics import ListAPIView
from .models import Product
from .serializers import ProductSerializer
from django.contrib.auth.models import User

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny] 

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny] 

# Lógica del Carro y Checkout
class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Obtiene o crea el carro del usuario autenticado
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
            items = cart.items.all()
        except Cart.DoesNotExist:
            return Response({"error": "No tienes un carro activo."}, status=status.HTTP_400_BAD_REQUEST)

        if not items.exists():
            return Response({"error": "El carro está vacío."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # INICIO DE TRANSACCIÓN ATÓMICA (Bloqueo de base de datos)
            with transaction.atomic():
                product_ids = items.values_list('product_id', flat=True)
                
                # select_for_update() bloquea las filas para que nadie más las compre al mismo tiempo
                products = Product.objects.select_for_update().filter(id__in=product_ids)
                product_dict = {p.id: p for p in products}

                total = 0
                order_items_to_create = []

                for item in items:
                    product = product_dict[item.product_id]
                    
                    if product.stock < item.quantity:
                        raise ValueError(f"Stock insuficiente para el producto: {product.name}.")
                    
                    # Descontar stock
                    product.stock -= item.quantity
                    product.save()

                    total += product.price * item.quantity

                    # Guardar precio histórico en la orden (Cumple la 3NF)
                    order_items_to_create.append(
                        OrderItem(product=product, historical_price=product.price, quantity=item.quantity)
                    )

                # Crear la orden final
                order = Order.objects.create(user=user, status='PAGADO', total=total)
                
                for oi in order_items_to_create:
                    oi.order = order
                OrderItem.objects.bulk_create(order_items_to_create)

                # Vaciar el carro tras la compra
                items.delete()

            return Response({
                "mensaje": "Compra realizada con éxito.",
                "orden_id": order.id,
                "total": total
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error interno al procesar el pago."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def index(request):
    return render(request, 'index.html')

class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"error": "Usuario y contraseña requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "El usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(username=username, password=password)
        return Response({"message": "Usuario registrado con éxito"}, status=status.HTTP_201_CREATED)
    
class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=404)

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)