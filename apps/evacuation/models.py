"""Defines the evacuation centers and their availability the app stores."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class EvacuationCenter(models.Model):
    STATUS_AVAILABLE = 'available'
    STATUS_FULL = 'full'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_FULL, 'Full'),
        (STATUS_CLOSED, 'Closed'),
    ]

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    current_occupancy = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
    )
    contact_person = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    supplies = models.TextField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='evacuation_centers',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblevacuationcenter'
        ordering = ['name']

    def clean(self):
        """Require both coordinates; range checks run through field validators."""
        super().clean()
        if self.latitude is None or self.longitude is None:
            raise ValidationError(
                'Both latitude and longitude are required for an evacuation center.'
            )

    def __str__(self):
        return self.name


class HazardZone(models.Model):
    """Defines a hazard zone (such as an earthquake or tsunami zone) that may affect evacuation planning."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    latitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='hazard_zones',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblhazardzone'
        ordering = ['name']

    def __str__(self):
        return self.name


class FloodProneArea(models.Model):
    """Defines a flood-prone area that may affect evacuation planning."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    latitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='flood_prone_areas',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblfloodpronearea'
        ordering = ['name']

    def __str__(self):
        return self.name
