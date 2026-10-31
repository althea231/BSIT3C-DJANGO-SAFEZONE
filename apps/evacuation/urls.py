from django.urls import path
from . import views

app_name = 'evacuation'

urlpatterns = [
    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC DISASTER-MAPPING ENDPOINTS (no authentication required)
    #
    # Citizens, residents and evacuees use these to instantly open the live
    # Leaflet map, search evacuation centers, check live capacities/statuses
    # and plan safe routes.
    # ─────────────────────────────────────────────────────────────────────────
    path('', views.evacuation_list_page, name='evacuation_list'),
    path('ajax/list/', views.evacuation_list_ajax, name='evacuation_list_ajax'),
    path('ajax/get/<int:pk>/', views.evacuation_get_ajax, name='evacuation_get_ajax'),
    path('ajax/evacuees/', views.public_evacuee_search_ajax, name='public_evacuee_search_ajax'),

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: safe check-in list for a single evacuation center.
    # Anonymous visitors may browse checked-in evacuees (safe fields only).
    # ─────────────────────────────────────────────────────────────────────────
    path('<int:center_id>/evacuees/', views.public_evacuee_list, name='public_evacuee_list'),
    # Legacy alias of the public check-in route, kept so pre-existing public
    # links, bookmarks and integrations keep resolving after the rename.
    path('<int:center_id>/evacuees/', views.public_evacuee_list, name='center_evacuees_public'),

    # ─────────────────────────────────────────────────────────────────────────
    # CREATOR / ADMIN ONLY ENDPOINTS (staff authentication required)
    #
    # Adding, editing or deleting evacuation centers is restricted to
    # authorized system creators / administrators. All of these views are
    # decorated with `@staff_required` (login + staff validation, 403 otherwise).
    # ─────────────────────────────────────────────────────────────────────────
    path('admin/save/', views.evacuation_save_ajax, name='evacuation_save_ajax'),
    path('admin/delete/<int:pk>/', views.evacuation_delete_ajax, name='evacuation_delete_ajax'),
    path('admin/evacuees/csv/', views.evacuee_report_csv, name='evacuee_report_csv'),
]
