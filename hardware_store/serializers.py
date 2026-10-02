from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Category, Product, Cart, CartItem

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        # Agregamos esta línea para saber si es proveedor (staff)
        token['is_staff'] = user.is_staff 
        return token

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'brand', 'price', 'stock', 'description', 'category', 'category_name', 'critical_stock', 'image']

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    price = serializers.ReadOnlyField(source='product.price')
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    # Usamos SerializerMethodField para evitar errores de nombres en la Base de Datos
    items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']

    def get_items(self, obj):
        items = CartItem.objects.filter(cart=obj)
        return CartItemSerializer(items, many=True).data