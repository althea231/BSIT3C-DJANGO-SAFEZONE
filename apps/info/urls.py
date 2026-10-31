from django.urls import path
from . import views

app_name = 'info'

urlpatterns = [
    # ─────────────────────────────────────────────────────────────────────────
    # EVACUEE MANAGEMENT ENDPOINTS (CREATOR / ADMIN ONLY)
    #
    # The evacuee list doubles as a monitoring view (sheltered counts, family
    # headcounts, PWD demographics) and its records are personal data, so every
    # endpoint here requires a staff (creator) session via `@staff_required`.
    # ─────────────────────────────────────────────────────────────────────────
    path('', views.info_list_page, name='info_list'),
    path('ajax/list/', views.info_list_ajax, name='info_list_ajax'),
    path('ajax/get/<int:pk>/', views.info_get_ajax, name='info_get_ajax'),
    path('ajax/save/', views.info_save_ajax, name='info_save_ajax'),
    path('ajax/delete/<int:pk>/', views.info_delete_ajax, name='info_delete_ajax'),
]
