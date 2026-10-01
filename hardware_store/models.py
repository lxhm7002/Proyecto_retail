from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    apellido_materno = models.CharField(max_length=150, blank=True, null=True, verbose_name="Apellido Materno")
    rut = models.CharField(max_length=12, unique=True, blank=True, null=True, verbose_name="RUT")
    
    ROLE_CHOICES = (
        ('CLIENTE', 'Cliente'),
        ('ADMIN_TI', 'Administrador de TI'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLIENTE')

    def get_full_name(self):
        materno = f" {self.apellido_materno}" if self.apellido_materno else ""
        return f"{self.first_name} {self.last_name}{materno}".strip()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)
    critical_stock = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to='productos/', null=True, blank=True)

    def __str__(self):
        return f"{self.brand} {self.name} - SKU: {self.sku}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product')
        ]

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    )
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE')
    total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Orden #{self.id} - Total: ${self.total} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT) 
    historical_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

