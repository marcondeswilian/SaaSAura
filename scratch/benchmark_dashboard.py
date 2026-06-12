import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from reservas.views import dashboard_view

# Find a user to authenticate request
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.first()

if user:
    factory = RequestFactory()
    request = factory.get('/painel/dashboard/')
    request.user = user
    
    request.session = {}
    from django.contrib.messages.storage.fallback import FallbackStorage
    setattr(request, '_messages', FallbackStorage(request))

    # Warm-up run
    dashboard_view(request)
    
    # 5 iterations
    runs = 5
    total_time = 0
    
    for i in range(runs):
        reset_queries()
        start_time = time.time()
        response = dashboard_view(request)
        elapsed_time = (time.time() - start_time) * 1000  # ms
        total_time += elapsed_time
        
    avg_time = total_time / runs
    query_count = len(connection.queries)
    
    print(f"BENCHMARK RESULTS (Warm Runs Average):")
    print(f"--------------------------------------")
    print(f"Average Response Time: {avg_time:.2f} ms")
    print(f"DB Query Count: {query_count}")
else:
    print("Error: No user found in database for authentication.")
