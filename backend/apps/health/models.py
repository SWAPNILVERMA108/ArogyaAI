from django.db import models


class HealthCategory(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=80)
    name_hi = models.CharField(max_length=80, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "health categories"

    def __str__(self):
        return self.name


class HealthTip(models.Model):
    category = models.ForeignKey(HealthCategory, on_delete=models.CASCADE, related_name="tips")
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=160)
    title_hi = models.CharField(max_length=160, blank=True)
    body = models.TextField()
    body_hi = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__order", "order", "id"]

    def __str__(self):
        return self.title
