from django.contrib import admin
from .models import Dealership, DealershipGroup

# Register your models here.

admin.site.register(Dealership)
admin.site.register(DealershipGroup)