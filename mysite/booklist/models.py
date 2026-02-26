from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    photo = models.ImageField(upload_to="profile_pics", verbose_name="Photo")

    favorite_books = models.ManyToManyField(to="bookshelf", blank=True,related_name="favored_by")
    about_me = models.TextField(verbose_name="About me", blank=True)

    # New privacy field
    is_profile_private = models.BooleanField(
        default=False,
        verbose_name="Private profile",
        help_text="If checked, only friends can see full profile info."
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.photo:
            img = Image.open(self.photo.path)
            min_side = min(img.width, img.height)
            left = (img.width - min_side) // 2
            top = (img.height - min_side) // 2
            right = left + min_side
            bottom = top + min_side
            img = img.crop((left, top, right, bottom))
            img = img.resize((150, 150), Image.LANCZOS)
            img.save(self.photo.path)

    def __str__(self):
        return self.username


class Author(models.Model):
    full_name = models.CharField(verbose_name="Name", null=False, blank=False)


    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    def __str__(self):
        return f"{self.full_name}"

class Category(models.Model):
    name = models.CharField(verbose_name="Name")

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Book(models.Model):
    google_books_id = models.CharField(unique=True, null=True, blank=True)
    authors = models.ManyToManyField(to="Author", verbose_name="Authors")
    title = models.CharField(verbose_name="Title")
    categories = models.ManyToManyField(to="Category", verbose_name="Categories")
    thumbnail = models.URLField(verbose_name="Cover URL", null=True, blank=True)
    description = models.TextField(verbose_name="Description")
    isbn_13 = models.CharField(unique=True, null=True, blank=True)
    isbn_10 = models.CharField(unique=True, null=True, blank=True)
    release_date = models.CharField(max_length=20, blank=True)

    def display_categories(self):
        return ", ".join(category.name for category in self.categories.all())

    def display_authors(self):
        return ", ".join(author.full_name for author in self.authors.all() if author.full_name)

    display_categories.short_description = "Category"

    def overall_rating(self):
        ratings = self.user_books.all()
        if not ratings.exists():
            return 0
        return sum(r.rating for r in ratings) / ratings.count()

    def __str__(self):
        return f"{self.display_authors()} - {self.title}"

class Bookshelf(models.Model):
    book = models.ForeignKey(to="Book", verbose_name="Book", on_delete=models.CASCADE, related_name="user_books")
    comment = models.CharField(verbose_name="Comment", blank=True, null=True)
    user = models.ForeignKey(to='booklist.CustomUser', on_delete=models.CASCADE, related_name="user_books")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    RATING = [(i, i) for i in range(1, 11)]

    rating = models.PositiveSmallIntegerField(verbose_name="Rating", choices=RATING, blank=True, null=True)

    TYPE = (
        ('b', "Book"),
        ('a', "Audiobook")
    )

    type = models.CharField(verbose_name="Type", choices=TYPE, default='b', blank=True, null=True)

    STATUS = (
        ('c', "Completed"),
        ('r', "Reading"),
        ('d', "Dropped"),
        ('t', "TBR")
    )

    status = models.CharField(verbose_name="Status", choices=STATUS, default='c', blank=True, null=True)

    def star_display(self):
        stars = round(self.rating / 2)
        return "★" * stars + "☆" * (5 - stars)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.book}"

class Post(models.Model):
    title = models.CharField(verbose_name="Title")
    author = models.ForeignKey(to='booklist.CustomUser', verbose_name="Content creator", on_delete=models.CASCADE)
    content = models.TextField(verbose_name="User content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(to='booklist.CustomUser', related_name="liked_posts", blank=True)

    class Meta:
        ordering = ['-created_at']

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(to='Post', on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(to='booklist.CustomUser', on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author}"











