from django.db import models


# Create your models here.
class File(models.Model):
    image = models.FileField(upload_to='post_images')

    def __str__(self):
        return "File"
