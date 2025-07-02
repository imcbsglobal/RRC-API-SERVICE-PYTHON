# urls.py - COMPLETE URL CONFIGURATION

from django.urls import path
from . import views

urlpatterns = [
    # Home endpoint to check if API is working
    path('', views.HomeView.as_view(), name='home'),

    # Simplified sync endpoint - clears table and inserts all data
    path('api/sync', views.SyncDataView.as_view(), name='sync_data'),

    # =============================================================================
    # CLIENT ENDPOINTS
    # =============================================================================
    # Get clients data with pagination (default 50 per page)
    path('api/clients', views.GetClientsView.as_view(), name='get_clients'),
    
    # Get ALL client data without pagination
    path('api/clients/all', views.GetAllClientsView.as_view(), name='get_all_clients'),

    # =============================================================================
    # MASTER ACCOUNT ENDPOINTS
    # =============================================================================
    # Get master accounts with pagination
    path('api/master', views.GetMasterView.as_view(), name='get_master'),
    
    # Get ALL master account data without pagination
    path('api/master/all', views.GetAllMasterView.as_view(), name='get_all_master'),

    # =============================================================================
    # PRODUCT ENDPOINTS
    # =============================================================================
    # Get ALL products without pagination (with optional search and category filters)
    path('api/products/all', views.GetAllProductsView.as_view(), name='get_all_products'),
]