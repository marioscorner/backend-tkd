# docs/serializers.py
from rest_framework import serializers
from .validators import validate_uploaded_file
from .models import BeltLevel as Level, Technique, Document

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["id", "name", "order", "is_public", "pdf"]

class TechniqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technique
        fields = ["id", "level", "name", "description", "image", "video_url"]

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file", "visibility", "created_at"]