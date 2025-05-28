from rest_framework import serializers
from .models import BookmarkedVideo


class BookmarkedVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookmarkedVideo
        fields = '__all__'