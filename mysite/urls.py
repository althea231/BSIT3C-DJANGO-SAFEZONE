"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC DISASTER-MAPPING ENDPOINTS — no authentication required
    # (live map, evacuation center search, capacities / statuses, safe routes).
    # ─────────────────────────────────────────────────────────────────────────
    path('', include('apps.core.urls')),

    # ─────────────────────────────────────────────────────────────────────────
    # RESTRICTED ENDPOINTS — authentication + staff (creator) required.
    # Monitoring dashboards (Dashboard), evacuee lists (Evacuees) and user
    # management live behind `@staff_required` / `@login_required` protected views.
    # ─────────────────────────────────────────────────────────────────────────
    path('users/', include('apps.users.urls')),
    path('info/', include('apps.info.urls')),
    path('evacuation/', include('apps.evacuation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)