"""
WSGI config for iccl_league_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project's root directory to the Python path
# This will be 'C:\Users\maste\Documents\Arpit\myproject'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print("*********project root*************", project_root)
print(sys.path)
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "iccl_league_app.settings"
)

application = get_wsgi_application()
