from django.contrib import admin
from .models import (
    DbrPatients, DbrBloodResults, DbrAppointments,
    DbrBloodTestReferences,
)


@admin.register(DbrPatients)
class PatientsAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'name', 'birth_date', 'sex', 'phone', 'created_at']
    list_filter = ['sex', 'created_at']
    search_fields = ['name', 'phone', 'id']
    readonly_fields = ['patient_id', 'created_at', 'updated_at']


@admin.register(DbrBloodResults)
class BloodResultsAdmin(admin.ModelAdmin):
    list_display = ['blood_result_id', 'patient_id', 'taken_at', 'ast', 'alt', 'afp', 'created_at']
    list_filter = ['taken_at', 'created_at']
    search_fields = ['patient_id__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'taken_at'


@admin.register(DbrAppointments)
class AppointmentsAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient_id', 'appointment_date', 'appointment_time', 'hospital', 'appointment_type', 'status']
    list_filter = ['appointment_type', 'status', 'appointment_date']
    search_fields = ['patient_id__name', 'hospital']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'appointment_date'


@admin.register(DbrBloodTestReferences)
class BloodTestReferencesAdmin(admin.ModelAdmin):
    list_display = ['reference_id', 'name', 'normal_range_min', 'normal_range_max', 'unit']
    search_fields = ['name']


