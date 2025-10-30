# backend-tkd-main/docs/urls.py
from django.urls import path
from .views import (
    LevelListCreateView, LevelDetailView,
    TechniqueListCreateView, TechniqueDetailView,
    DocumentListCreateView, DocumentDetailView,
)

urlpatterns = [
    # Levels
    path("levels/", LevelListCreateView.as_view()),
    path("levels/<int:pk>/", LevelDetailView.as_view()),

    # Techniques
    path("techniques/", TechniqueListCreateView.as_view()),
    path("techniques/<int:pk>/", TechniqueDetailView.as_view()),

    # Documents
    path("documents/", DocumentListCreateView.as_view()),
    path("documents/<int:pk>/", DocumentDetailView.as_view()),
]
