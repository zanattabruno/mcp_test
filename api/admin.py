from django.contrib import admin
from .models import Client, Meeting


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'email', 'phone', 'created_at')
	search_fields = ('name', 'email', 'phone')


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'client', 'start_time', 'end_time', 'location')
	list_filter = ('client',)

# Register your models here.
