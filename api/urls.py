# urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Home endpoint to check if API is working
    path('', views.HomeView.as_view(), name='home'),

    # Simplified sync endpoint - clears table and inserts all data
    path('api/sync', views.SyncDataView.as_view(), name='sync_data'),

    # Get clients data with pagination (default 50 per page)
    path('api/clients', views.GetClientsView.as_view(), name='get_clients'),
    
    # NEW: Get ALL client data without pagination
    path('api/clients/all', views.GetAllClientsView.as_view(), name='get_all_clients'),

    # Manually refresh cache
    path('api/refresh-cache', views.RefreshCacheView.as_view(), name='refresh_cache'),

    # Get sync status and statistics (FIXED)
    path('api/status', views.SyncStatusView.as_view(), name='sync_status'),
]