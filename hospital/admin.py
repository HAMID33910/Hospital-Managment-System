from django.contrib import admin
from .models import (Profile, Doctor, Patient, Appointment, Room,
                     RoomAllocation, Medicine, Prescription, PrescriptionItem,
                     Billing, BillingItem)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'consultation_fee', 'is_active']
    list_filter = ['specialization', 'is_active']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone', 'blood_group', 'is_admitted']
    list_filter = ['gender', 'blood_group', 'is_admitted']
    search_fields = ['first_name', 'last_name', 'phone']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_date']
    date_hierarchy = 'appointment_date'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'price_per_day', 'status', 'capacity', 'current_occupancy']
    list_filter = ['room_type', 'status']


@admin.register(RoomAllocation)
class RoomAllocationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'room', 'check_in', 'check_out', 'is_active']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'stock_quantity', 'price_per_unit', 'expiry_date']
    list_filter = ['category', 'requires_prescription']
    search_fields = ['name', 'brand']


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'prescribed_date', 'is_active']
    inlines = [PrescriptionItemInline]


class BillingItemInline(admin.TabularInline):
    model = BillingItem
    extra = 1


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ['patient', 'total_amount', 'paid_amount', 'status', 'bill_date']
    list_filter = ['status']
    inlines = [BillingItemInline]
