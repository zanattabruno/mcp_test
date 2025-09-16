from rest_framework import serializers
from .models import Client, Meeting


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'created_at']
        read_only_fields = ['id', 'created_at']


class MeetingSerializer(serializers.ModelSerializer):
    client_detail = ClientSerializer(source='client', read_only=True)

    class Meta:
        model = Meeting
        fields = [
            'id', 'client', 'client_detail', 'title', 'start_time', 'end_time',
            'location', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'client_detail']

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        client = attrs.get('client', getattr(self.instance, 'client', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_time': 'end_time must be after start_time'})

        if start and end and client:
            qs = Meeting.objects.filter(client=client)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if Meeting.overlaps(qs, start, end):
                raise serializers.ValidationError('Client already has a meeting in this time range')
        return attrs