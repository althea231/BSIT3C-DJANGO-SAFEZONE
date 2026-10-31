from django.contrib import admin

from .models import EvacuationCenter, FloodProneArea, HazardZone


@admin.register(EvacuationCenter)
class EvacuationCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'capacity', 'current_occupancy', 'status', 'is_active')
    list_filter = ('status',)
    search_fields = ('name', 'address', 'contact_person')


@admin.register(HazardZone)
class HazardZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'latitude', 'longitude', 'is_active')
    search_fields = ('name', 'description')


@admin.register(FloodProneArea)
class FloodProneAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'latitude', 'longitude', 'is_active')
    search_fields = ('name', 'description')
