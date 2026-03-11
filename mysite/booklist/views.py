from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.generic import ListView, DetailView, UpdateView
from django.views.generic.edit import FormMixin
from .models import Book, Bookshelf, Category, CustomUser, Post
from .utils import store_books_by_title, store_books_by_author
from .forms import CustomUserCreateForm, CustomUserChangeForm, PostCreateUpdateForm, BookshelfCreateUpdateForm, \
    FavoriteUpdateForm, CommentForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


# About page view
def about_page(request):
    return render(request, template_name="about.html")


class BookSearchListView(ListView):
    """
    Displays search results for books.
    Allows searching either by book title or author.
    Results are paginated.
    """
    model = Book
    template_name = 'search.html'
    context_object_name = 'books'
    paginate_by = 24

    def get_queryset(self):
        # Get query parameters from URL
        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'title')  # 'title' or 'author'

        # If no query is provided return an empty queryset
        if not query:
            return Book.objects.none()

        # Call utility functions that fetch/store books from external APIs by author or title
        if search_type == 'author':
            return store_books_by_author(query)
        else:
            return store_books_by_title(query)

    def get_context_data(self, **kwargs):
        # Pass search parameters back to the template
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['search_type'] = self.request.GET.get('type', 'title')
        return context


class SignUpView(generic.CreateView):
    """
    Handles new user registration.
    Uses a custom user creation form and redirects to login after success.
    """
    form_class = CustomUserCreateForm
    template_name = "signup.html"
    success_url = reverse_lazy("login")


class PublicProfileView(LoginRequiredMixin, DetailView):
    """
    Displays a public user profile page.
    The profile is accessed using the username in the URL.
    """
    model = CustomUser
    template_name = "public_profile.html"
    slug_field = "username"  # Use username in URL
    slug_url_kwarg = "username"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        # Add user's favorite books to the template context
        context = super().get_context_data(**kwargs)
        context['favorite_books'] = self.object.favorite_books.all()
        return context


class ProfileUpdateView(LoginRequiredMixin, generic.UpdateView):
    """
    Allows a logged-in user to update their own profile information.
    """
    form_class = CustomUserChangeForm
    template_name = 'profile.html'

    def get_object(self, queryset=None):
        # Only allow editing the current logged-in user
        return self.request.user

    def get_success_url(self):
        # Redirect to the public profile page after update
        return reverse('public_profile', kwargs={'username': self.request.user.username})


class BookListView(generic.ListView):
    """
    Displays a paginated list of all books stored in the database.
    """
    model = Book
    template_name = "books.html"
    context_object_name = "books"
    paginate_by = 24


class BookDetailView(generic.DetailView):
    """
    Shows detailed information about a single book.
    Also checks if the current user has already added the book to their bookshelf.
    """
    model = Book
    template_name = "book.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        book = self.object
        user = self.request.user

        # Determine if the book is already in the user's bookshelf
        is_in_bookshelf = False
        if user.is_authenticated:
            is_in_bookshelf = Bookshelf.objects.filter(
                user=user,
                book=book
            ).exists()

        context["is_in_bookshelf"] = is_in_bookshelf
        return context


class CategoryListView(generic.ListView):
    """
    Displays all book categories grouped alphabetically.
    Categories that do not start with a letter are grouped under '#'.
    """
    model = Category
    template_name = "categories.html"
    context_object_name = "categories"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch all categories, ordered alphabetically
        categories = Category.objects.all().order_by('name')

        # Initialize dictionary
        categories_dict = {}

        # Group categories by their first letter
        for category in categories:
            first_letter = category.name[0].upper()
            if not first_letter.isalpha():
                first_letter = '#'
            categories_dict.setdefault(first_letter, []).append(category)

        context['categories_dict'] = dict(sorted(categories_dict.items()))
        return context


class CategoryBookListView(generic.ListView):
    """
    Displays all books belonging to a specific category.
    """
    model = Book
    template_name = "category_books.html"
    context_object_name = "books"
    paginate_by = 24

    def get_queryset(self):
        # Filter books by category id
        category_id = self.kwargs.get('pk')
        return Book.objects.filter(categories__id=category_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('pk')
        context['category'] = Category.objects.get(pk=category_id)
        return context


class PostViewList(generic.ListView):
    """
    Displays a list of forum posts created by users.
    """
    model = Post
    template_name = "posts.html"
    context_object_name = "posts"
    paginate_by = 20


class PostDetailList(FormMixin, DetailView):
    """
    Displays a single post along with its comments.
    Also allows users to submit a comment on the same page.
    """
    model = Post
    template_name = "post.html"
    context_object_name = "post"
    form_class = CommentForm

    # URL to redirect to after successful comment
    def get_success_url(self):
        return reverse("post", kwargs={"pk": self.object.pk})


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Provide comment form to template
        if 'form' not in context:
            context['form'] = self.get_form()
        # Add comments
        context['comments'] = self.object.comments.order_by('created_at')
        return context

    # Handle POST using FormMixin methods
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # Assign post and author before saving
        form.instance.post = self.get_object()
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)


class PostCreateView(LoginRequiredMixin, generic.CreateView):
    """
    Allows logged-in users to create a new post.
    """
    model = Post
    template_name = "post_form.html"
    form_class = PostCreateUpdateForm

    def form_valid(self, form):
        # Automatically set the post author
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to the newly created post
        return reverse('post', kwargs={'pk': self.object.pk})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    """
    Allows users to edit their own posts.
    """
    model = Post
    template_name = "post_form.html"
    form_class = PostCreateUpdateForm

    def get_success_url(self):
        return reverse("post", kwargs={"pk": self.object.pk})

    def test_func(self):
        # Ensure only the post author can edit it
        return self.get_object().author == self.request.user


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    """
    Allows users to delete their own posts.
    """
    model = Post
    template_name = "post_delete.html"
    context_object_name = "post"
    success_url = reverse_lazy('posts')

    def test_func(self):
        # Only the author can delete the post
        return self.get_object().author == self.request.user


@login_required
def toggle_like_ajax(request, pk):
    """
    Handles AJAX requests for liking/unliking a post.
    Returns JSON with updated like status and like count.
    """
    post = Post.objects.get(pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'total_likes': post.likes.count()
    })


class BookshelfListView(LoginRequiredMixin, generic.ListView):
    """
    Displays the logged-in user's personal bookshelf.
    """
    model = Bookshelf
    template_name = "bookshelf.html"
    context_object_name = "bookshelf"
    paginate_by = 20

    def get_queryset(self):
        # Only show books added by the current user
        return Bookshelf.objects.filter(user=self.request.user)


class BookshelfDetailView(LoginRequiredMixin, generic.DetailView):
    """
    Displays detailed information about a specific bookshelf entry.
    """
    model = Bookshelf
    template_name = "bookshelf_book.html"
    context_object_name = "bookshelf_book"

    def get_queryset(self):
        # Restrict access to user's own bookshelf entries
        return Bookshelf.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse("bookshelf")


class BookshelfCreateView(LoginRequiredMixin, generic.CreateView):
    """
    Allows a user to manually add a book to their bookshelf.
    Prevents duplicate entries using database constraints.
    """
    model = Bookshelf
    template_name = "bookshelf_form.html"
    form_class = BookshelfCreateUpdateForm
    success_url = reverse_lazy('bookshelf')

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            # Show warning if the book already exists in bookshelf
            messages.warning(self.request, "You already added this book to your bookshelf.")
            return redirect('bookshelf')


class AddToBookshelfView(LoginRequiredMixin, generic.View):
    """
    Quick action view used to add a book to the user's bookshelf directly from the book page.
    """

    def post(self, request, pk):
        book = Book.objects.get(pk=pk)

        Bookshelf.objects.get_or_create(
            user=request.user,
            book=book
        )

        return redirect("book", pk=pk)


class BookshelfUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    """
    Allows users to update information about a book in their bookshelf
    (e.g., reading status, comment, rating).
    """
    model = Bookshelf
    template_name = "bookshelf_form.html"
    form_class = BookshelfCreateUpdateForm

    def get_success_url(self):
        return reverse("bookshelf")

    def test_func(self):
        # Ensure users can only edit their own bookshelf items
        return self.get_object().user == self.request.user


class BookshelfDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    """
    Allows users to remove a book from their bookshelf.
    """
    model = Bookshelf
    template_name = "bookshelf_delete.html"
    context_object_name = "bookshelf_book"
    success_url = reverse_lazy('bookshelf')

    def get_queryset(self):
        # Only allow the current user to delete their own books
        return Bookshelf.objects.filter(user=self.request.user)

    def test_func(self):
        return self.get_object().user == self.request.user


class FavoriteUpdateView(LoginRequiredMixin, UpdateView):
    """
    Allows users to update their list of favorite books.
    """
    model = CustomUser
    form_class = FavoriteUpdateForm
    template_name = "add_favorite.html"

    def get_object(self, queryset=None):
        # User can only edit their own favorites
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        # Redirect to /profile/<username> after adding a favorite
        return reverse('public_profile', kwargs={'username': self.request.user.username})
