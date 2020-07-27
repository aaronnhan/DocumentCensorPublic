from rest_framework import serializers
from .models import File

#Used to serialize data between frontend and backend
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

    def process_image(self):
        File.objects.last().process_image()