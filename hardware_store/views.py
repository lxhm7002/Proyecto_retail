from django.shortcuts import render
from django.db import transaction
from django.contrib.auth import get_user_model  # Importación dinámica para tu modelo personalizado
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import CustomTokenObtainPairSerializer, CategorySerializer, ProductSerializer, CartSerializer

# Carga tu usuario personalizado en lugar del básico de Django
User = get_user_model()

def index(request):
    return render(request, 'index.html')

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

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        product_id = request.data.get('product_id') or request.data.get('id')
        if not product_id:
            return Response({"error": "Falta el ID del producto."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "El producto no existe en la BD."}, status=status.HTTP_404_NOT_FOUND)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        
        if cart_item.quantity + 1 > product.stock:
            return Response({"error": f"No puedes agregar más. Solo hay {product.stock} unidades en stock."}, status=status.HTTP_400_BAD_REQUEST)
            
        cart_item.quantity += 1
        cart_item.save()
        return Response(CartSerializer(cart).data)

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
                        raise ValueError(f"Stock insuficiente para {item.product.name}. Tienes {item.quantity} en el carro pero solo {item.product.stock} en stock.")
                    
                    # Descontamos el stock
                    item.product.stock -= item.quantity
                    item.product.save()
                    
                    # Creamos el item de la orden
                    order_item = OrderItem(order=order, product=item.product, quantity=item.quantity)
                    
                    # ¡SOLUCIÓN!: Le pasamos el precio a tu columna "historical_price"
                    if hasattr(order_item, 'historical_price'):
                        order_item.historical_price = item.product.price
                    elif hasattr(order_item, 'price'):
                        order_item.price = item.product.price
                        
                    order_item.save()
                    
                    # Sumamos al total general
                    total += item.product.price * item.quantity

                # Asignamos el total de la orden
                if hasattr(order, 'total_amount'):
                    order.total_amount = total
                elif hasattr(order, 'total'):
                    order.total = total
                    
                order.save()
                
                # Vaciamos el carro tras la compra exitosa
                items.delete()
                
                return Response({"mensaje": "Compra realizada con éxito"}, status=status.HTTP_201_CREATED)
                
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Falla en Base de Datos: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)