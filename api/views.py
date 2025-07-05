# views.py - ULTRA-OPTIMIZED VERSION FOR HIGH PERFORMANCE
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
import psycopg2.extras  # For PostgreSQL optimizations

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
    """ULTRA-OPTIMIZED sync endpoint with advanced bulk operations"""

    def post(self, request):
        start_time = datetime.now()
        try:
            # Parse request data
            data = json.loads(request.body)
            table_name = data.get('table', 'rrc_clients')
            records = data.get('data', [])

            # Validate table name
            valid_tables = ['rrc_clients', 'acc_master', 'acc_product']
            if table_name not in valid_tables:
                return Response({
                    'success': False,
                    'error': f'Invalid table name. Valid tables: {valid_tables}'
                }, status=400)

            logger.info(f"Sync request - Table: {table_name}, Records: {len(records)}")

            if not records:
                return Response({
                    'success': False,
                    'error': 'No data provided'
                }, status=400)

            # Process the sync with ultra-optimizations
            with transaction.atomic():
                # Step 1: Ultra-fast table clearing
                self._ultra_fast_truncate(table_name)
                logger.info(f"Table {table_name} truncated")

                # Step 2: Ultra-optimized bulk insert
                inserted_count = self._ultra_bulk_insert(table_name, records)
                logger.info(f"Inserted {inserted_count} records into {table_name}")

                # Step 3: Minimal cache clearing (only if needed)
                self._smart_cache_clear(table_name)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return Response({
                'success': True,
                'message': f'Ultra-fast sync completed for {table_name}',
                'table': table_name,
                'records_processed': inserted_count,
                'table_cleared': True,
                'duration_seconds': round(duration, 2),
                'records_per_second': round(inserted_count / duration if duration > 0 else 0, 2),
                'timestamp': end_time.isoformat(),
                'optimization': 'ULTRA_MODE'
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

    def _ultra_fast_truncate(self, table_name):
        """Ultra-fast table clearing with optimizations"""
        try:
            with connection.cursor() as cursor:
                # Disable autocommit for better performance
                cursor.execute('BEGIN')
                
                # Use TRUNCATE with CASCADE and RESTART IDENTITY for maximum speed
                cursor.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE')
                
                # Commit immediately
                cursor.execute('COMMIT')
                
                logger.info(f"Ultra-fast truncate completed for {table_name}")
        except Exception as e:
            logger.error(f"Error in ultra-fast truncate for {table_name}: {str(e)}")
            # Fallback to regular DELETE if TRUNCATE fails
            with connection.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{table_name}"')
            raise

    def _ultra_bulk_insert(self, table_name, records):
        """Ultra-optimized bulk insert using COPY or VALUES method"""
        if not records:
            return 0

        try:
            # Get columns from first record
            columns = list(records[0].keys())
            
            # Choose the best insertion method based on database backend
            if 'postgresql' in connection.settings_dict['ENGINE'].lower():
                return self._postgresql_copy_insert(table_name, columns, records)
            else:
                return self._values_bulk_insert(table_name, columns, records)
                
        except Exception as e:
            logger.error(f"Error in ultra bulk insert: {str(e)}")
            raise

    def _postgresql_copy_insert(self, table_name, columns, records):
        """Ultra-fast PostgreSQL COPY method"""
        try:
            import io
            
            # Prepare data for COPY
            output = io.StringIO()
            
            for record in records:
                row_data = []
                for col in columns:
                    value = record.get(col)
                    if value is None:
                        row_data.append('\\N')  # PostgreSQL NULL representation
                    elif isinstance(value, datetime):
                        row_data.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(value, str):
                        # Escape special characters for COPY
                        escaped = value.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
                        row_data.append(escaped)
                    else:
                        row_data.append(str(value))
                
                output.write('\t'.join(row_data) + '\n')
            
            output.seek(0)
            
            # Use raw connection for COPY
            with connection.cursor() as cursor:
                # Get the raw psycopg2 cursor
                raw_cursor = cursor.cursor
                
                # Prepare column names
                column_names = ', '.join([f'"{col}"' for col in columns])
                
                # Execute COPY FROM STDIN
                copy_sql = f'COPY "{table_name}" ({column_names}) FROM STDIN WITH (FORMAT text, DELIMITER E\'\\t\', NULL \'\\N\')'
                raw_cursor.copy_expert(copy_sql, output)
                
                return len(records)
                
        except Exception as e:
            logger.error(f"PostgreSQL COPY failed: {str(e)}")
            # Fallback to VALUES method
            return self._values_bulk_insert(table_name, columns, records)

    def _values_bulk_insert(self, table_name, columns, records):
        """Ultra-fast VALUES bulk insert method"""
        try:
            # Process in optimal batches
            batch_size = 2000  # Optimal batch size for most databases
            total_inserted = 0
            
            column_names = ', '.join([f'"{col}"' for col in columns])
            
            with connection.cursor() as cursor:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    
                    # Build VALUES clause
                    values_parts = []
                    params = []
                    
                    for record in batch:
                        value_placeholders = []
                        for col in columns:
                            value = record.get(col)
                            if value is None:
                                value_placeholders.append('NULL')
                            elif isinstance(value, datetime):
                                value_placeholders.append('%s')
                                params.append(value.strftime('%Y-%m-%d'))
                            else:
                                value_placeholders.append('%s')
                                params.append(value)
                        
                        values_parts.append(f"({', '.join(value_placeholders)})")
                    
                    # Single INSERT with multiple VALUES
                    if values_parts:
                        values_clause = ', '.join(values_parts)
                        insert_sql = f'INSERT INTO "{table_name}" ({column_names}) VALUES {values_clause}'
                        
                        cursor.execute(insert_sql, params)
                        total_inserted += len(batch)
                        
                        # Log progress for large datasets
                        if len(records) > 5000:
                            logger.info(f"Batch progress: {total_inserted}/{len(records)} records inserted")
            
            return total_inserted
            
        except Exception as e:
            logger.error(f"VALUES bulk insert failed: {str(e)}")
            # Final fallback to executemany
            return self._fallback_executemany(table_name, columns, records)

    def _fallback_executemany(self, table_name, columns, records):
        """Fallback method using executemany (slower but reliable)"""
        try:
            column_names = ', '.join([f'"{col}"' for col in columns])
            placeholders = ', '.join(['%s'] * len(columns))
            
            # Prepare data
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
            
            # Execute in smaller batches
            batch_size = 1000
            total_inserted = 0
            
            with connection.cursor() as cursor:
                query = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
                
                for i in range(0, len(values_list), batch_size):
                    batch = values_list[i:i + batch_size]
                    cursor.executemany(query, batch)
                    total_inserted += len(batch)
            
            return total_inserted
            
        except Exception as e:
            logger.error(f"Fallback executemany failed: {str(e)}")
            raise

    def _smart_cache_clear(self, table_name):
        """Smart cache clearing - only clear when necessary"""
        try:
            # Only clear cache if it exists and is relevant
            cache_keys_to_clear = [
                f'{table_name}_*',  # Table-specific cache
                f'*{table_name}*',  # Any cache containing table name
            ]
            
            # In production, implement pattern-based cache clearing
            # For now, just clear all cache but log it
            cache.clear()
            logger.info(f"Smart cache cleared for table: {table_name}")
            
        except Exception as e:
            logger.warning(f"Cache clearing failed (non-critical): {str(e)}")


# =============================================================================
# OPTIMIZED CLIENT APIs
# =============================================================================

class GetClientsView(APIView):
    """Optimized client data retrieval with enhanced caching"""

    def get(self, request):
        start_time = datetime.now()
        try:
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 5000)
            search = request.GET.get('search', '').strip()

            # Enhanced cache strategy
            cache_key = f'rrc_clients_v2_p{page}_s{page_size}_{hash(search)}'
            last_updated_key = 'rrc_clients_last_updated_v2'

            cached_data = cache.get(cache_key)
            last_updated = cache.get(last_updated_key)

            # Check cache validity
            cache_duration_minutes = getattr(settings, 'CLIENT_DATA_CACHE_MINUTES', 30)
            cache_valid = False

            if cached_data and last_updated:
                cache_age = datetime.now() - last_updated
                cache_valid = cache_age < timedelta(minutes=cache_duration_minutes)

            if cache_valid:
                logger.info(f"Returning cached client data (page {page})")
                response_data = cached_data.copy()
                response_data.update({
                    'from_cache': True,
                    'cache_expires_in_minutes': int((timedelta(minutes=cache_duration_minutes) - cache_age).total_seconds() / 60)
                })
                return Response(response_data)

            # Fetch fresh data with optimizations
            logger.info(f"Fetching optimized client data from database (page {page})")
            result = self._fetch_clients_optimized(page, page_size, search)

            # Cache the data
            current_time = datetime.now()
            cache.set(cache_key, result, timeout=cache_duration_minutes * 60)
            cache.set(last_updated_key, current_time, timeout=cache_duration_minutes * 60)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result.update({
                'last_updated': current_time.isoformat(),
                'from_cache': False,
                'next_refresh_in_minutes': cache_duration_minutes,
                'query_duration_seconds': round(duration, 3),
                'optimization': 'ENHANCED'
            })

            return Response(result)

        except Exception as e:
            logger.error(f"Error fetching clients: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch clients: {str(e)}'
            }, status=500)

    def _fetch_clients_optimized(self, page, page_size, search):
        """Optimized client data fetching with better SQL"""
        try:
            with connection.cursor() as cursor:
                # Use prepared statements and optimized queries
                base_where = '1=1'
                params = []

                if search:
                    base_where += ' AND ("name" ILIKE %s OR "code" ILIKE %s OR "district" ILIKE %s)'
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])

                # Optimized count query
                count_query = f'SELECT COUNT(*) FROM "rrc_clients" WHERE {base_where}'
                cursor.execute(count_query, params)
                total_records = cursor.fetchone()[0]

                # Optimized data query with explicit column selection
                offset = (page - 1) * page_size
                data_query = f'''
                    SELECT 
                        "code", "name", "address", "branch", "district", "state",
                        "software", "mobile", "installationdate", "priorty",
                        "directdealing", "rout", "amc", "amcamt", "accountcode",
                        "address3", "lictype", "clients", "sp", "nature"
                    FROM "rrc_clients"
                    WHERE {base_where}
                    ORDER BY "name"
                    LIMIT %s OFFSET %s
                '''
                
                params.extend([page_size, offset])
                cursor.execute(data_query, params)
                
                # Optimized result processing
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Optimized date handling
                    if record.get('installationdate') and hasattr(record['installationdate'], 'isoformat'):
                        record['installationdate'] = record['installationdate'].isoformat()
                    
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


class GetAllClientsView(APIView):
    """Optimized all clients data retrieval"""

    def get(self, request):
        start_time = datetime.now()
        try:
            search = request.GET.get('search', '').strip()
            
            logger.info("Fetching ALL client data from database (optimized)")
            
            with connection.cursor() as cursor:
                # Optimized query
                if search:
                    query = '''
                        SELECT "code", "name", "address", "branch", "district", "state",
                               "software", "mobile", "installationdate", "priorty",
                               "directdealing", "rout", "amc", "amcamt", "accountcode",
                               "address3", "lictype", "clients", "sp", "nature"
                        FROM "rrc_clients"
                        WHERE "name" ILIKE %s OR "code" ILIKE %s OR "district" ILIKE %s
                        ORDER BY "name"
                    '''
                    search_param = f'%{search}%'
                    cursor.execute(query, [search_param, search_param, search_param])
                else:
                    query = '''
                        SELECT "code", "name", "address", "branch", "district", "state",
                               "software", "mobile", "installationdate", "priorty",
                               "directdealing", "rout", "amc", "amcamt", "accountcode",
                               "address3", "lictype", "clients", "sp", "nature"
                        FROM "rrc_clients"
                        ORDER BY "name"
                    '''
                    cursor.execute(query)
                
                # Optimized result processing
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Handle dates efficiently
                    if record.get('installationdate') and hasattr(record['installationdate'], 'isoformat'):
                        record['installationdate'] = record['installationdate'].isoformat()
                    
                    results.append(record)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return Response({
                'success': True,
                'data': results,
                'total_records': len(results),
                'search_applied': bool(search),
                'search_term': search if search else None,
                'query_duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'optimization': 'ENHANCED',
                'warning': 'This endpoint returns ALL data - use pagination for better performance'
            })

        except Exception as e:
            logger.error(f"Error fetching all clients: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch all clients: {str(e)}'
            }, status=500)



# =============================================================================
# OPTIMIZED MASTER ACCOUNT APIs
# =============================================================================

class GetMasterView(APIView):
    """Optimized master account data retrieval with enhanced caching - Balance > 0 only"""

    def get(self, request):
        start_time = datetime.now()
        try:
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 5000)
            search = request.GET.get('search', '').strip()

            # Enhanced cache strategy
            cache_key = f'acc_master_v2_p{page}_s{page_size}_{hash(search)}_balance_gt_0'
            last_updated_key = 'acc_master_last_updated_v2_balance_gt_0'

            cached_data = cache.get(cache_key)
            last_updated = cache.get(last_updated_key)

            # Check cache validity
            cache_duration_minutes = getattr(settings, 'MASTER_DATA_CACHE_MINUTES', 30)
            cache_valid = False

            if cached_data and last_updated:
                cache_age = datetime.now() - last_updated
                cache_valid = cache_age < timedelta(minutes=cache_duration_minutes)

            if cache_valid:
                logger.info(f"Returning cached master data (page {page}) - Balance > 0")
                response_data = cached_data.copy()
                response_data.update({
                    'from_cache': True,
                    'cache_expires_in_minutes': int((timedelta(minutes=cache_duration_minutes) - cache_age).total_seconds() / 60)
                })
                return Response(response_data)

            # Fetch fresh data with optimizations
            logger.info(f"Fetching optimized master data from database (page {page}) - Balance > 0")
            result = self._fetch_master_optimized(page, page_size, search)

            # Cache the data
            current_time = datetime.now()
            cache.set(cache_key, result, timeout=cache_duration_minutes * 60)
            cache.set(last_updated_key, current_time, timeout=cache_duration_minutes * 60)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result.update({
                'last_updated': current_time.isoformat(),
                'from_cache': False,
                'next_refresh_in_minutes': cache_duration_minutes,
                'query_duration_seconds': round(duration, 3),
                'optimization': 'ENHANCED',
                'filter_applied': 'Balance > 0'
            })

            return Response(result)

        except Exception as e:
            logger.error(f"Error fetching master accounts: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch master accounts: {str(e)}'
            }, status=500)

    def _fetch_master_optimized(self, page, page_size, search):
        """Optimized master account data fetching with better SQL - Balance > 0 only"""
        try:
            with connection.cursor() as cursor:
                # Base WHERE clause with balance > 0 condition
                base_where = '(COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) > 0'
                params = []

                if search:
                    base_where += ' AND ("name" ILIKE %s OR "code" ILIKE %s OR "place" ILIKE %s)'
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])

                # Optimized count query with balance filter
                count_query = f'SELECT COUNT(*) FROM "acc_master" WHERE {base_where}'
                cursor.execute(count_query, params)
                total_records = cursor.fetchone()[0]

                # Optimized data query with explicit column selection + BALANCE CALCULATION + BALANCE FILTER
                offset = (page - 1) * page_size
                data_query = f'''
                    SELECT 
                        "code", "name", "super_code", "opening_balance", "debit", 
                        "credit", "place", "phone2", "openingdepartment",
                        (COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) AS balance
                    FROM "acc_master"
                    WHERE {base_where}
                    ORDER BY "name"
                    LIMIT %s OFFSET %s
                '''
                
                params.extend([page_size, offset])
                cursor.execute(data_query, params)
                
                # Optimized result processing
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Convert Decimal fields to float for JSON serialization
                    decimal_fields = ['opening_balance', 'debit', 'credit', 'balance']
                    for field in decimal_fields:
                        if record.get(field) is not None:
                            record[field] = float(record[field])
                    
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
                    'records_on_page': len(results),
                    'filter_info': {
                        'balance_filter': 'Only records with balance > 0',
                        'calculation': 'opening_balance + debit - credit > 0'
                    }
                }

        except Exception as e:
            logger.error(f"Database error in master fetch: {str(e)}")
            raise


class GetAllMasterView(APIView):
    """Optimized all master accounts data retrieval - Balance > 0 only"""

    def get(self, request):
        start_time = datetime.now()
        try:
            search = request.GET.get('search', '').strip()
            
            logger.info("Fetching ALL master account data from database (optimized) - Balance > 0")
            
            with connection.cursor() as cursor:
                # Base WHERE clause with balance > 0 condition
                balance_condition = '(COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) > 0'
                
                # Optimized query with balance filter
                if search:
                    query = f'''
                        SELECT "code", "name", "super_code", "opening_balance", "debit",
                               "credit", "place", "phone2", "openingdepartment",
                               (COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) AS balance
                        FROM "acc_master"
                        WHERE {balance_condition}
                        AND ("name" ILIKE %s OR "code" ILIKE %s OR "place" ILIKE %s)
                        ORDER BY "name"
                    '''
                    search_param = f'%{search}%'
                    cursor.execute(query, [search_param, search_param, search_param])
                else:
                    query = f'''
                        SELECT "code", "name", "super_code", "opening_balance", "debit",
                               "credit", "place", "phone2", "openingdepartment",
                               (COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) AS balance
                        FROM "acc_master"
                        WHERE {balance_condition}
                        ORDER BY "name"
                    '''
                    cursor.execute(query)
                
                # Optimized result processing
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Convert Decimal fields to float for JSON serialization
                    decimal_fields = ['opening_balance', 'debit', 'credit', 'balance']
                    for field in decimal_fields:
                        if record.get(field) is not None:
                            record[field] = float(record[field])
                    
                    results.append(record)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return Response({
                'success': True,
                'data': results,
                'total_records': len(results),
                'search_applied': bool(search),
                'search_term': search if search else None,
                'query_duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'optimization': 'ENHANCED',
                'filter_info': {
                    'balance_filter': 'Only records with balance > 0',
                    'calculation': 'opening_balance + debit - credit > 0'
                },
                'warning': 'This endpoint returns ALL data with balance > 0 - use pagination for better performance'
            })

        except Exception as e:
            logger.error(f"Error fetching all master accounts: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch all master accounts: {str(e)}'
            }, status=500)

# =============================================================================
# OPTIMIZED PRODUCT APIs
# =============================================================================

class GetAllProductsView(APIView):
    """Optimized all products data retrieval with filtering capabilities"""

    def get(self, request):
        start_time = datetime.now()
        try:
            search = request.GET.get('search', '').strip()
            category = request.GET.get('category', '').strip()
            company = request.GET.get('company', '').strip()
            brand = request.GET.get('brand', '').strip()
            
            # Enhanced cache strategy for products
            cache_params = f"{hash(search)}_{hash(category)}_{hash(company)}_{hash(brand)}"
            cache_key = f'acc_product_v2_{cache_params}'
            last_updated_key = 'acc_product_last_updated_v2'

            cached_data = cache.get(cache_key)
            last_updated = cache.get(last_updated_key)

            # Check cache validity (shorter cache for products as they might change more frequently)
            cache_duration_minutes = getattr(settings, 'PRODUCT_DATA_CACHE_MINUTES', 15)
            cache_valid = False

            if cached_data and last_updated:
                cache_age = datetime.now() - last_updated
                cache_valid = cache_age < timedelta(minutes=cache_duration_minutes)

            if cache_valid:
                logger.info("Returning cached product data")
                response_data = cached_data.copy()
                response_data.update({
                    'from_cache': True,
                    'cache_expires_in_minutes': int((timedelta(minutes=cache_duration_minutes) - cache_age).total_seconds() / 60)
                })
                return Response(response_data)
            
            logger.info("Fetching ALL product data from database (optimized)")
            
            with connection.cursor() as cursor:
                # Build dynamic query with filters
                where_conditions = []
                params = []

                if search:
                    where_conditions.append('("name" ILIKE %s OR "code" ILIKE %s)')
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])

                if category:
                    where_conditions.append('"catagory" ILIKE %s')
                    params.append(f'%{category}%')

                if company:
                    where_conditions.append('"company" ILIKE %s')
                    params.append(f'%{company}%')

                if brand:
                    where_conditions.append('"brand" ILIKE %s')
                    params.append(f'%{brand}%')

                where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'

                # Optimized query
                query = f'''
                    SELECT "code", "name", "catagory", "unit", "taxcode",
                           "company", "product", "brand", "text6"
                    FROM "acc_product"
                    WHERE {where_clause}
                    ORDER BY "name"
                '''
                
                cursor.execute(query, params)
                
                # Optimized result processing
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    results.append(record)

            # Cache the results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result_data = {
                'success': True,
                'data': results,
                'total_records': len(results),
                'filters': {
                    'search': search if search else None,
                    'category': category if category else None,
                    'company': company if company else None,
                    'brand': brand if brand else None
                },
                'filters_applied': bool(search or category or company or brand),
                'query_duration_seconds': round(duration, 3),
                'timestamp': datetime.now().isoformat(),
                'optimization': 'ENHANCED',
                'from_cache': False
            }

            # Cache the data
            current_time = datetime.now()
            cache.set(cache_key, result_data, timeout=cache_duration_minutes * 60)
            cache.set(last_updated_key, current_time, timeout=cache_duration_minutes * 60)

            result_data.update({
                'last_updated': current_time.isoformat(),
                'next_refresh_in_minutes': cache_duration_minutes
            })

            return Response(result_data)

        except Exception as e:
            logger.error(f"Error fetching all products: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch all products: {str(e)}'
            }, status=500)