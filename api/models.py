from django.db import models
from django.core.exceptions import ValidationError


class Client(models.Model):
	name = models.CharField(max_length=200)
	email = models.EmailField(unique=True)
	phone = models.CharField(max_length=50, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} <{self.email}>"


class Meeting(models.Model):
	client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='meetings')
	title = models.CharField(max_length=200)
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()
	location = models.CharField(max_length=200, blank=True)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['start_time']
		constraints = [
			models.CheckConstraint(check=models.Q(end_time__gt=models.F('start_time')), name='meeting_end_after_start'),
		]

	def clean(self):
		if self.end_time <= self.start_time:
			raise ValidationError({'end_time': 'end_time must be after start_time'})

	def __str__(self):
		return f"{self.title} with {self.client}"

	@staticmethod
	def overlaps(qs, start, end):
		return qs.filter(start_time__lt=end, end_time__gt=start).exists()

# Create your models here.
