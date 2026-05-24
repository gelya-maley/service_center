from django.contrib import admin
from .models import (
    EmployeeProfile, ServiceType, Service, Client,
    DeviceType, SparePart, Order, OrderService, OrderSparePart
)

class OrderServiceInline(admin.TabularInline):
    model = OrderService
    extra = 1

class OrderSparePartInline(admin.TabularInline):
    model = OrderSparePart
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'master', 'device', 'status', 'order_date', 'total_cost')
    list_filter = ('status', 'order_date', 'master')
    search_fields = ('client__full_name', 'client_problem')
    inlines = [OrderServiceInline, OrderSparePartInline]
    readonly_fields = ('order_date',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'price')
    list_filter = ('service_type',)
    search_fields = ('name',)

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'birth_date', 'age')
    search_fields = ('full_name', 'phone')

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'phone')

admin.site.register(ServiceType)
admin.site.register(DeviceType)
admin.site.register(SparePart)