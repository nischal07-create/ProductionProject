import os
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from allauth.socialaccount.models import SocialApp
apps = []
for s in SocialApp.objects.all():
    apps.append({'id': s.id, 'provider': s.provider, 'name': s.name, 'client_id': s.client_id, 'secret': s.secret, 'sites': [site.id for site in s.sites.all()]})
print(json.dumps(apps, indent=2))
