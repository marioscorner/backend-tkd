from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BeltLevelViewSet, TechniqueViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'levels', BeltLevelViewSet, basename='levels')
router.register(r'techniques', TechniqueViewSet, basename='techniques')
router.register(r'documents', DocumentViewSet, basename='documents')

urlpatterns = [ path('', include(router.urls)) ]
