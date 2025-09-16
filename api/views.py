from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, Meeting
from .serializers import ClientSerializer, MeetingSerializer


class ClientViewSet(viewsets.ModelViewSet):
	queryset = Client.objects.all()
	serializer_class = ClientSerializer
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['email', 'name']
	search_fields = ['name', 'email', 'phone']
	ordering_fields = ['name', 'created_at']

	def get_queryset(self):
		return Client.objects.all()


class MeetingViewSet(viewsets.ModelViewSet):
	queryset = Meeting.objects.select_related('client').all()
	serializer_class = MeetingSerializer
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
	filterset_fields = ['client', 'title']
	ordering_fields = ['start_time', 'end_time', 'created_at']

	def get_queryset(self):
		qs = Meeting.objects.select_related('client')
		start = self.request.query_params.get('start')
		end = self.request.query_params.get('end')
		if start:
			qs = qs.filter(end_time__gt=start)
		if end:
			qs = qs.filter(start_time__lt=end)
		return qs

# Create your views here.
