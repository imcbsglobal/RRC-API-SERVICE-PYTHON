# views.py - SIMPLIFIED VERSION
import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.db import connection, transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class HomeView(View):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return JsonResponse({
                "status": "API is live ✅",
                "database": "Database connected ✅",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JsonResponse({
                "status": "API is live ✅",
                "database": f"Database connection failed ❌: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })


@method_decorator(csrf_exempt, name='dispatch')
class SyncDataView(APIView):
    def post(self, request):
        try:
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

            if not records:
                return Response({
                    'success': False,
                    'error': 'No data provided'
                }, status=400)

            # Process sync
            with transaction.atomic():
                # Clear table
                with connection.cursor() as cursor:
                    cursor.execute(f'DELETE FROM "{table_name}"')
                
                # Insert new data
                inserted_count = self._bulk_insert(table_name, records)

            return Response({
                'success': True,
                'message': f'Sync completed for {table_name}',
                'table': table_name,
                'records_processed': inserted_count,
                'timestamp': datetime.now().isoformat()
            })

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

    def _bulk_insert(self, table_name, records):
        if not records:
            return 0

        columns = list(records[0].keys())
        column_names = ', '.join([f'"{col}"' for col in columns])
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Prepare data
        values_list = []
        for record in records:
            values = []
            for col in columns:
                value = record.get(col)
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d') if value else None
                values.append(value)
            values_list.append(tuple(values))

        # Insert in batches
        batch_size = 1000
        total_inserted = 0
        
        with connection.cursor() as cursor:
            query = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
            
            for i in range(0, len(values_list), batch_size):
                batch = values_list[i:i + batch_size]
                cursor.executemany(query, batch)
                total_inserted += len(batch)
        
        return total_inserted


class GetClientsView(APIView):
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 1000)
            search = request.GET.get('search', '').strip()

            with connection.cursor() as cursor:
                # Build query
                where_clause = '1=1'
                params = []

                if search:
                    where_clause += ' AND ("name" ILIKE %s OR "code" ILIKE %s OR "district" ILIKE %s)'
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])

                # Get total count
                count_query = f'SELECT COUNT(*) FROM "rrc_clients" WHERE {where_clause}'
                cursor.execute(count_query, params)
                total_records = cursor.fetchone()[0]

                # Get data
                offset = (page - 1) * page_size
                data_query = f'''
                    SELECT * FROM "rrc_clients"
                    WHERE {where_clause}
                    ORDER BY "name"
                    LIMIT %s OFFSET %s
                '''
                
                params.extend([page_size, offset])
                cursor.execute(data_query, params)
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    if record.get('installationdate') and hasattr(record['installationdate'], 'isoformat'):
                        record['installationdate'] = record['installationdate'].isoformat()
                    results.append(record)

                total_pages = (total_records + page_size - 1) // page_size

                return Response({
                    'success': True,
                    'data': results,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_records': total_records,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }
                })

        except Exception as e:
            logger.error(f"Error fetching clients: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch clients: {str(e)}'
            }, status=500)


class GetAllClientsView(APIView):
    def get(self, request):
        try:
            search = request.GET.get('search', '').strip()
            
            with connection.cursor() as cursor:
                if search:
                    query = '''
                        SELECT * FROM "rrc_clients"
                        WHERE "name" ILIKE %s OR "code" ILIKE %s OR "district" ILIKE %s
                        ORDER BY "name"
                    '''
                    search_param = f'%{search}%'
                    cursor.execute(query, [search_param, search_param, search_param])
                else:
                    cursor.execute('SELECT * FROM "rrc_clients" ORDER BY "name"')
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    if record.get('installationdate') and hasattr(record['installationdate'], 'isoformat'):
                        record['installationdate'] = record['installationdate'].isoformat()
                    results.append(record)

            return Response({
                'success': True,
                'data': results,
                'total_records': len(results),
                'search_applied': bool(search),
                'search_term': search if search else None
            })

        except Exception as e:
            logger.error(f"Error fetching all clients: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch all clients: {str(e)}'
            }, status=500)


class GetMasterView(APIView):
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 1000)
            search = request.GET.get('search', '').strip()

            with connection.cursor() as cursor:
                # Only get records with balance > 0
                where_clause = '(COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) > 0'
                params = []

                if search:
                    where_clause += ' AND ("name" ILIKE %s OR "code" ILIKE %s OR "place" ILIKE %s)'
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])

                # Get total count
                count_query = f'SELECT COUNT(*) FROM "acc_master" WHERE {where_clause}'
                cursor.execute(count_query, params)
                total_records = cursor.fetchone()[0]

                # Get data with balance calculation
                offset = (page - 1) * page_size
                data_query = f'''
                    SELECT *, 
                           (COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) AS balance
                    FROM "acc_master"
                    WHERE {where_clause}
                    ORDER BY "name"
                    LIMIT %s OFFSET %s
                '''
                
                params.extend([page_size, offset])
                cursor.execute(data_query, params)
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Convert decimals to float
                    decimal_fields = ['opening_balance', 'debit', 'credit', 'balance']
                    for field in decimal_fields:
                        if record.get(field) is not None:
                            record[field] = float(record[field])
                    
                    results.append(record)

                total_pages = (total_records + page_size - 1) // page_size

                return Response({
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
                    'filter_info': 'Only records with balance > 0'
                })

        except Exception as e:
            logger.error(f"Error fetching master accounts: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch master accounts: {str(e)}'
            }, status=500)


class GetAllMasterView(APIView):
    def get(self, request):
        try:
            search = request.GET.get('search', '').strip()
            
            with connection.cursor() as cursor:
                # Only get records with balance > 0
                balance_condition = '(COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) > 0'
                
                if search:
                    query = f'''
                        SELECT *, 
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
                        SELECT *, 
                               (COALESCE("opening_balance", 0) + COALESCE("debit", 0) - COALESCE("credit", 0)) AS balance
                        FROM "acc_master"
                        WHERE {balance_condition}
                        ORDER BY "name"
                    '''
                    cursor.execute(query)
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Convert decimals to float
                    decimal_fields = ['opening_balance', 'debit', 'credit', 'balance']
                    for field in decimal_fields:
                        if record.get(field) is not None:
                            record[field] = float(record[field])
                    
                    results.append(record)

            return Response({
                'success': True,
                'data': results,
                'total_records': len(results),
                'search_applied': bool(search),
                'search_term': search if search else None,
                'filter_info': 'Only records with balance > 0'
            })

        except Exception as e:
            logger.error(f"Error fetching all master accounts: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch all master accounts: {str(e)}'
            }, status=500)


class GetAllProductsView(APIView):
    def get(self, request):
        try:
            search = request.GET.get('search', '').strip()
            category = request.GET.get('category', '').strip()
            company = request.GET.get('company', '').strip()
            brand = request.GET.get('brand', '').strip()
            
            with connection.cursor() as cursor:
                # Build query with filters
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

                query = f'''
                    SELECT * FROM "acc_product"
                    WHERE {where_clause}
                    ORDER BY "name"
                '''
                
                cursor.execute(query, params)
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    results.append(record)

            return Response({
                'success': True,
                'data': results,
                'total_records': len(results),
                'filters': {
                    'search': search if search else None,
                    'category': category if category else None,
                    'company': company if company else None,
                    'brand': brand if brand else None
                },
                'filters_applied': bool(search or category or company or brand)
            })

        except Exception as e:
            logger.error(f"Error fetching all products: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to fetch all products: {str(e)}'
            }, status=500)