"""Reusable permission helpers for the SafeZone two-tier access model.

Public access (no login): live map, evacuation center directory, capacity
checks and safe route planning.

Creator / Admin access (login + staff): monitoring dashboards, evacuee
records, user management and all write operations.

The single source of truth for "may this user manage SafeZone data?" lives
here so every view, mixin and test validates against the same rule.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def is_creator(user):
    """Return True when the user is an authorized SafeZone creator/admin.

    Creators are staff members (or superusers) allowed to monitor the system,
    view restricted metrics and modify evacuation / hazard data.
    Anonymous users and regular evacuees are never creators.
    """
    return bool(user is not None and user.is_authenticated and (user.is_staff or user.is_superuser))


def staff_required(view_func):
    """Decorator for staff/creator-only views.

    - Anonymous users are redirected to the login page (``login_url``).
    - Authenticated users that are not creators receive a ``403 Forbidden``.
    """

    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if not is_creator(request.user):
            raise PermissionDenied('Staff access required to perform this action.')
        return view_func(request, *args, **kwargs)

    return _wrapped_view
