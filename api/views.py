# views.py - OPTIMIZED VERSION
import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.db import connection, DatabaseError, transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import psycopg2.extras  # For faster bulk inserts

# Setup logging
logger = logging.getLogger(__name__)


class HomeView(View):
    def get(self, request):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")  # Simple DB check
            db_status = "Database connected ✅"
        except DatabaseError as e:
            db_status = f"Database connection failed ❌: {str(e)}"

        data = {
            "status": "API is live ✅",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class SyncDataView(APIView):
    """OPTIMIZED sync endpoint with bulk operations"""

    def post(self, request):
        start_time = datetime.now()
        try:
            # Parse request data
            data = json.loads(request.body)
            table_name = data.get('table', 'rrc_clients')
            records = data.get('data', [])

            logger.info(
                f"Sync request - Table: {table_name}, Records: {len(records)}")

            if not records:
                return Response({
                    'success': False,
                    'error': 'No data provided'
                }, status=400)

            # Process the sync in a transaction with optimizations
            with transaction.atomic():
                # Use TRUNCATE instead of DELETE for faster clearing
                self._truncate_table(table_name)
                logger.info(f"Table {table_name} truncated")

                # Bulk insert with optimized method
                inserted_count = self._bulk_insert_optimized(
                    table_name, records)
                logger.info(
                    f"Inserted {inserted_count} records into {table_name}")

                # Clear cache efficiently
                self._clear_related_cache()
                logger.info("Cache cleared after sync")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return Response({
                'success': True,
                'message': f'Sync completed successfully',
                'records_processed': inserted_count,
                'table_cleared': True,
                'duration_seconds': round(duration, 2),
                'records_per_second': round(inserted_count / duration if duration > 0 else 0, 2),
                'timestamp': end_time.isoformat()
            }, status=200)

        except json.JSONDecodeError:
            return Response({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)

        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            return Response({
                'success': False,
                'error': f'Sync failed: {str(e)}'
            }, status=500)

    def _truncate_table(self, table_name):
        """Use TRUNCATE for faster table clearing"""
        try:
            with connection.cursor() as cursor:
                # TRUNCATE is much faster than DELETE for clearing entire tables
                cursor.execute(
                    f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY')
                logger.info(f"Table {table_name} truncated successfully")
        except Exception as e:
            logger.error(f"Error truncating table {table_name}: {str(e)}")
            # Fallback to DELETE if TRUNCATE fails
            with connection.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{table_name}"')
            raise

    def _bulk_insert_optimized(self, table_name, records):
        """Optimized bulk insert using PostgreSQL COPY or execute_values"""
        if not records:
            return 0

        try:
            # Get columns from first record
            columns = list(records[0].keys())

            # Prepare data more efficiently
            values_list = []
            for record in records:
                values = []
                for col in columns:
                    value = record.get(col)
                    if value is None:
                        values.append(None)
                    elif isinstance(value, datetime):
                        values.append(value.strftime('%Y-%m-%d'))
                    else:
                        values.append(value)
                values_list.append(tuple(values))

            # Use PostgreSQL's faster bulk insert method
            with connection.cursor() as cursor:
                # Method 1: Use execute_values (fastest for PostgreSQL)
                column_names = ', '.join([f'"{col}"' for col in columns])
                placeholders = ', '.join(['%s'] * len(columns))

                # Use execute_values for better performance
                from psycopg2.extras import execute_values
                query = f'INSERT INTO "{table_name}" ({column_names}) VALUES %s'
                execute_values(
                    cursor.cursor,  # Get the underlying psycopg2 cursor
                    query,
                    values_list,
                    template=None,
                    page_size=1000  # Process in batches of 1000
                )

                return len(values_list)

        except Exception as e:
            logger.error(f"Error in optimized bulk insert: {str(e)}")
            # Fallback to original method
            return self._insert_records_fallback(table_name, records)

    def _insert_records_fallback(self, table_name, records):
        """Fallback method if optimized insert fails"""
        if not records:
            return 0

        try:
            with connection.cursor() as cursor:
                columns = list(records[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join([f'"{col}"' for col in columns])

                insert_query = f'''
                    INSERT INTO "{table_name}" ({column_names})
                    VALUES ({placeholders})
                '''

                # Prepare data for bulk insert
                values_list = []
                for record in records:
                    values = []
                    for col in columns:
                        value = record.get(col)
                        if value is None:
                            values.append(None)
                        elif isinstance(value, datetime):
                            values.append(value.strftime('%Y-%m-%d'))
                        else:
                            values.append(value)
                    values_list.append(tuple(values))

                # Execute in batches for better performance
                batch_size = 1000
                for i in range(0, len(values_list), batch_size):
                    batch = values_list[i:i + batch_size]
                    cursor.executemany(insert_query, batch)

                return len(values_list)

        except Exception as e:
            logger.error(f"Error inserting records: {str(e)}")
            raise

    def _clear_related_cache(self):
        """Clear all related cache keys efficiently"""
        cache_keys = [
            'rrc_clients_data',
            'rrc_clients_last_updated',
            f'rrc_clients_count',
        ]
        cache.delete_many(cache_keys)


class GetClientsView(APIView):
    """OPTIMIZED get all client data with better caching and pagination"""

    def get(self, request):
        start_time = datetime.now()
        try:
            # Get query parameters
            page = int(request.GET.get('page', 1))
            # Max 5000 records per page
            page_size = min(int(request.GET.get('page_size', 1000)), 5000)
            search = request.GET.get('search', '').strip()

            # Check cache first
            cache_key = f'rrc_clients_data_p{page}_s{page_size}_{hash(search)}'
            last_updated_key = 'rrc_clients_last_updated'

            cached_data = cache.get(cache_key)
            last_updated = cache.get(last_updated_key)

            # Check if cache is still valid
            cache_duration_minutes = getattr(
                settings, 'CLIENT_DATA_CACHE_MINUTES', 30)
            cache_valid = False

            if cached_data and last_updated:
                cache_age = datetime.now() - last_updated
                cache_valid = cache_age < timedelta(
                    minutes=cache_duration_minutes)

            if cache_valid:
                logger.info(f"Returning cached client data (page {page})")
                response_data = cached_data.copy()
                response_data.update({
                    'from_cache': True,
                    'cache_expires_in_minutes': int((timedelta(minutes=cache_duration_minutes) - cache_age).total_seconds() / 60)
                })
                return Response(response_data)

            # Fetch fresh data from database with pagination
            logger.info(
                f"Fetching fresh client data from database (page {page})")
            result = self._fetch_clients_paginated(page, page_size, search)

            # Cache the data
            current_time = datetime.now()
            cache.set(cache_key, result, timeout=cache_duration_minutes * 60)
            cache.set(last_updated_key, current_time,
                      timeout=cache_duration_minutes * 60)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result.update({
                'last_updated': current_time.isoformat(),
                'from_cache': False,
                'next_refresh_in_minutes': cache_duration_minutes,
                'query_duration_seconds': round(duration, 3)
            })

            return Response(result)

        except Exception as e:
            logger.error(f"Error fetching clients: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch clients: {str(e)}'
            }, status=500)

    def _fetch_clients_paginated(self, page, page_size, search):
        """Fetch client data with pagination and search"""
        try:
            with connection.cursor() as cursor:
                # Count query for pagination
                count_query = 'SELECT COUNT(*) FROM "rrc_clients"'
                where_clause = ''
                params = []

                if search:
                    where_clause = '''WHERE "name" ILIKE %s 
                                     OR "code" ILIKE %s 
                                     OR "district" ILIKE %s'''
                    search_param = f'%{search}%'
                    params = [search_param, search_param, search_param]
                    count_query += ' ' + where_clause

                cursor.execute(count_query, params)
                total_records = cursor.fetchone()[0]

                # Data query with pagination
                offset = (page - 1) * page_size
                data_query = '''
                    SELECT 
                        "code", "name", "address", "branch", "district", "state",
                        "software", "mobile", "installationdate", "priorty",
                        "directdealing", "rout", "amc", "amcamt", "accountcode",
                        "address3", "lictype", "clients", "sp", "nature"
                    FROM "rrc_clients"
                '''

                if where_clause:
                    data_query += ' ' + where_clause

                data_query += f' ORDER BY "name" LIMIT %s OFFSET %s'
                params.extend([page_size, offset])

                cursor.execute(data_query, params)
                columns = [col[0] for col in cursor.description]

                results = []
                for row in cursor.fetchall():
                    record = {}
                    for i, value in enumerate(row):
                        column_name = columns[i]
                        if value and column_name in ['installationdate']:
                            if hasattr(value, 'isoformat'):
                                record[column_name] = value.isoformat()
                            else:
                                record[column_name] = str(value)
                        elif value is None:
                            record[column_name] = None
                        else:
                            record[column_name] = value
                    results.append(record)

                # Calculate pagination info
                total_pages = (total_records + page_size - 1) // page_size

                return {
                    'success': True,
                    'data': results,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_records': total_records,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    },
                    'records_on_page': len(results)
                }

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise


class RefreshCacheView(APIView):
    """Manually refresh the cache"""

    def post(self, request):
        try:
            # Clear all related cache
            cache.clear()  # Clear all cache
            logger.info("All cache cleared")

            return Response({
                'success': True,
                'message': 'Cache cleared successfully - fresh data will be fetched on next request',
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Cache refresh failed: {str(e)}'
            }, status=500)


class SyncStatusView(APIView):
    """Get current sync status and statistics"""

    def get(self, request):
        try:
            start_time = datetime.now()

            # Get database record count efficiently
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM "rrc_clients"')
                total_records = cursor.fetchone()[0]

            # Get cache info
            cached_data = cache.get('rrc_clients_data')
            last_updated = cache.get('rrc_clients_last_updated')

            cache_status = "No cache" if not cached_data else "Cached"
            cache_age_minutes = 0

            if last_updated:
                cache_age = datetime.now() - last_updated
                cache_age_minutes = int(cache_age.total_seconds() / 60)

            # Get database performance info
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname, 
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes
                    FROM pg_stat_user_tables 
                    WHERE tablename = 'rrc_clients'
                """)

                stats = cursor.fetchone()
                db_stats = {}
                if stats:
                    db_stats = {
                        'inserts': stats[2],
                        'updates': stats[3],
                        'deletes': stats[4]
                    }

            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds()

            return Response({
                'success': True,
                'database_records': total_records,
                'cache_status': cache_status,
                'cache_age_minutes': cache_age_minutes,
                'last_cache_update': last_updated.isoformat() if last_updated else None,
                'database_stats': db_stats,
                'query_duration_seconds': round(query_time, 3),
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Status check failed: {str(e)}'
            }, status=500)
