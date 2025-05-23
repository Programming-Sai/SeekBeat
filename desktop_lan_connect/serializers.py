from rest_framework import serializers
from .models import DeviceProfile, SongProfile

class DeviceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceProfile
        fields = '__all__'

class SongProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongProfile
        fields = '__all__'
