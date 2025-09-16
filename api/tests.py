from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Client, Meeting
from datetime import datetime, timedelta, timezone


class APITest(TestCase):
	def setUp(self):
		self.client_api = APIClient()

	def test_create_client_and_meeting(self):
		r = self.client_api.post('/api/clients/', {
			'name': 'Acme Corp',
			'email': 'contact@acme.test',
			'phone': '+1-555-000'
		}, format='json')
		self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.content)
		client_id = r.data['id']

		start = datetime.now(timezone.utc) + timedelta(hours=1)
		end = start + timedelta(hours=2)
		r2 = self.client_api.post('/api/meetings/', {
			'client': client_id,
			'title': 'Kickoff',
			'start_time': start.isoformat(),
			'end_time': end.isoformat(),
			'location': 'Zoom'
		}, format='json')
		self.assertEqual(r2.status_code, status.HTTP_201_CREATED, r2.content)

		# Overlap should fail
		r3 = self.client_api.post('/api/meetings/', {
			'client': client_id,
			'title': 'Overlap',
			'start_time': start.isoformat(),
			'end_time': (start + timedelta(minutes=30)).isoformat(),
		}, format='json')
		self.assertEqual(r3.status_code, status.HTTP_400_BAD_REQUEST)

		# Listing meetings
		r4 = self.client_api.get('/api/meetings/?client=' + str(client_id))
		self.assertEqual(r4.status_code, status.HTTP_200_OK)
		self.assertEqual(len(r4.data), 1)

# Create your tests here.
