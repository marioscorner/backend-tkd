from rest_framework import serializers
from .models import BeltLevel, Technique, Document

class TechniqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technique
        fields = ["id", "level", "name", "description", "image", "video_url"]

class BeltLevelSerializer(serializers.ModelSerializer):
    techniques = TechniqueSerializer(many=True, read_only=True)

    class Meta:
        model = BeltLevel
        fields = ["id", "name", "order", "is_public", "pdf", "techniques"]

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file", "visibility", "created_at"]
