from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class BeltLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_public = models.BooleanField(default=True)  # visible para anónimos si abres API pública
    pdf = models.FileField(upload_to="levels/pdfs/", blank=True, null=True)  # luego migraremos a S3

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.order} · {self.name}"

class Technique(models.Model):
    level = models.ForeignKey(BeltLevel, on_delete=models.CASCADE, related_name="techniques")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="techniques/images/", blank=True, null=True)  # luego S3
    video_url = models.URLField(blank=True)

    class Meta:
        unique_together = ("level", "name")
        ordering = ["id"]

    def __str__(self):
        return f"{self.level.name} · {self.name}"

class Document(models.Model):
    """
    Documentos varios (circulares, normas, hojas de inscripción, etc.)
    visibility: quién puede verlo.
    """
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        ALUMNO = "alumno", "Alumno"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/files/")
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.ALUMNO)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return f"{self.title} ({self.visibility})"
