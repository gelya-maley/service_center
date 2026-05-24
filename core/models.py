from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
import datetime

# Валидатор для телефона
phone_regex = RegexValidator(
    regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$',
    message="Телефон должен быть в формате: +375 (29) 123-45-67"
)

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    phone = models.CharField(max_length=20, validators=[phone_regex])
    specialization = models.CharField(max_length=100, verbose_name="Специализация")
    hire_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.specialization}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=200)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, default="шт.", help_text="шт., час, услуга")
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.price} руб.)"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile', null=True, blank=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, validators=[phone_regex])
    address = models.TextField()
    passport_data = models.CharField(max_length=100, blank=True, verbose_name="Паспортные данные")
    birth_date = models.DateField(verbose_name="Дата рождения")  # Обязательное поле!

    def age(self):
        today = timezone.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    def save(self, *args, **kwargs):
        if self.age() < 18:
            raise ValueError("Клиент должен быть старше 18 лет")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

class DeviceType(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.brand} {self.name}".strip()

class SparePart(models.Model):
    name = models.CharField(max_length=200)
    compatible_devices = models.ManyToManyField(DeviceType, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    master = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='orders')
    device = models.ForeignKey(DeviceType, on_delete=models.SET_NULL, null=True)
    services = models.ManyToManyField(Service, through='OrderService', related_name='orders')
    spare_parts = models.ManyToManyField(SparePart, through='OrderSparePart', blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    client_problem = models.TextField(verbose_name="Описание проблемы")

    def total_cost(self):
        services_cost = sum(item.service.price * item.quantity for item in self.orderservice_set.all())
        parts_cost = sum(item.spare_part.price * item.quantity for item in self.ordersparepart_set.all())
        return services_cost + parts_cost

    def __str__(self):
        return f"Заказ #{self.id} - {self.client.full_name}"

class OrderService(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class OrderSparePart(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)