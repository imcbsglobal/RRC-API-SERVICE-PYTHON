# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Home endpoint to check if API is working
    path('', views.HomeView.as_view(), name='home'),

    # Simplified sync endpoint - clears table and inserts all data
    path('api/sync', views.SyncDataView.as_view(), name='sync_data'),

    # Get all clients data (with caching)
    path('api/clients', views.GetClientsView.as_view(), name='get_clients'),

    # Manually refresh cache
    path('api/refresh-cache', views.RefreshCacheView.as_view(), name='refresh_cache'),

    # Get sync status and statistics
    path('api/status', views.SyncStatusView.as_view(), name='sync_status'),
]
