"""Per-user scoping helpers for SafeZone data.

The application uses a two-tier access model:

* PUBLIC — anonymous visitors may read the live evacuation center directory,
  hazard zones and flood-prone areas (used by the public Leaflet map, search
  and "Plan Safe Route" features).
* CREATOR / ADMIN — staff members manage evacuation centers, hazard zones and
  evacuee records for the monitored area.

The helpers below translate the requesting user into a queryset:

* Staff / creators always receive the full dataset they administer.
* Authenticated non-staff users only receive records they created themselves.
* Anonymous (public) visitors only receive the read-only operational dataset
  needed to use the public mapping features.
"""

from django.shortcuts import get_object_or_404

from apps.evacuation.models import EvacuationCenter, FloodProneArea, HazardZone
from apps.info.models import Info


def _is_creator(user):
    return bool(
        user is not None
        and user.is_authenticated
        and (user.is_staff or user.is_superuser)
    )


def scoped_infos(user):
    """Evacuee personal records: staff see all, others only their own."""
    if _is_creator(user):
        return Info.objects.all()
    if user.is_authenticated:
        return Info.objects.filter(user=user)
    # Personal evacuee data is never exposed to anonymous visitors.
    return Info.objects.none()


def scoped_info(user, pk):
    return get_object_or_404(scoped_infos(user), pk=pk)


def scoped_evacuation_centers(user):
    """Live evacuation center directory: public visitors and creators see all."""
    if _is_creator(user) or not user.is_authenticated:
        return EvacuationCenter.objects.all()
    return EvacuationCenter.objects.filter(user=user)


def scoped_evacuation_center(user, pk):
    if _is_creator(user) or not user.is_authenticated:
        return get_object_or_404(EvacuationCenter.objects.all(), pk=pk)
    return get_object_or_404(EvacuationCenter.objects.filter(user=user), pk=pk)


def scoped_hazard_zones(user):
    """Hazard zones used for public route avoidance: public + creators see all."""
    if _is_creator(user) or not user.is_authenticated:
        return HazardZone.objects.all()
    return HazardZone.objects.filter(user=user)


def scoped_flood_prone_areas(user):
    """Flood-prone areas used for public route avoidance: public + creators see all."""
    if _is_creator(user) or not user.is_authenticated:
        return FloodProneArea.objects.all()
    return FloodProneArea.objects.filter(user=user)
