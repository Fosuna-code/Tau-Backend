from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit

class Category(models.Model):
    """
    Genres for movies (e.g., Sci-Fi, Action).
    A Movie can have many Categories.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="A URL-friendly version of the name, e.g., 'sci-fi'")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=200)

    # 1. The "Source" Files (Uploaded by Admin)
    # These go to S3, e.g., s3://bucket/movies/posters/matrix_master.jpg
    poster_original = models.ImageField(upload_to='movies/posters/')
    backdrop_original = models.ImageField(upload_to='movies/backdrops/')

    # 2. The "Virtual" Optimized Files (Generated on the fly)
    # This creates a 300x450 thumbnail for the UI
    poster_mobile = ImageSpecField(
        source='poster_original',
        processors=[ResizeToFit(160, 240)], # Cut to fit exact dimensions
        format='WEBP',                       # Modern, small format
        options={'quality': 80}              # Compress to 80%
    )
    poster_desktop = ImageSpecField(
        source='poster_original',
        processors=[ResizeToFit(220, 330)], # Cut to fit exact dimensions
        format='WEBP',                       # Modern, small format
        options={'quality': 80}              # Compress to 80%
    )

    # This creates a 1920x1080 version for the header (downscaling 4K)
    backdrop_large = ImageSpecField(
        source='backdrop_original',
        processors=[ResizeToFit(1920, 1080)],
        format='WEBP',
        options={'quality': 85}
    )


    description = models.TextField()
    year = models.IntegerField()


    # 1. The Database Field: Store simple integers (e.g., 105)
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")

    # ... other fields ...

    # 2. The Logic: Convert 105 -> "1h 45min" on the fly
    @property
    def duration_formatted(self):
        if not self.duration_minutes:
            return ""
            
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}min"

    is_new = models.BooleanField(default=False, help_text='is this movie new?')
    is_active = models.BooleanField(default=True, help_text="Is this movie visible to users?")
    is_student_production = models.BooleanField(
        default=False, 
        help_text="Is this a 'Made by Students' film?"
    )
    categories = models.ManyToManyField(
        Category, 
        related_name='movies', 
        blank=True
    )
    is_from_festival = models.BooleanField(default=False, help_text='is this movie from a festival?')

    def __str__(self):
        return self.title
