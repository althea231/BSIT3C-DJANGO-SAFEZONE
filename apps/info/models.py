"""Defines the personal information (name, age, address, and email) the app stores."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Info(models.Model):
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(150)])
    address = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True)
    pwd = models.BooleanField(default=False)
    family_head = models.CharField(max_length=255, blank=True)
    evacuation_center = models.ForeignKey(
        'evacuation.EvacuationCenter',
        related_name='evacuees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Evacuation center this person is checked in to.',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='infos',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblinfo'
        ordering = ['name']

    def __str__(self):
        return self.name
