from django.urls import path
from . import views

urlpatterns = [
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    # PUBLIC ENTRY POINT: no authentication required. The root URL always
    # renders the public live evacuation map and center list, regardless of
    # whether the visitor is anonymous or a logged-in staff creator.
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
