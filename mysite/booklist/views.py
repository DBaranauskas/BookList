from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.generic import ListView, DetailView, UpdateView
from django.views.generic.edit import FormMixin

from .models import Book, Bookshelf, Category, CustomUser,Post
from .utils import store_books_by_title, store_books_by_author
from .forms import CustomUserCreateForm, CustomUserChangeForm, PostCreateUpdateForm, BookshelfCreateUpdateForm,FavoriteUpdateForm, CommentForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Create your views here.

def about_page(request):
    return render(request, template_name="about.html")

class BookSearchListView(ListView):
    model = Book
    template_name = 'search.html'
    context_object_name = 'books'
    paginate_by = 24

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'title')  # 'title' or 'author'

        if not query:
            return Book.objects.none()  # empty queryset if no search

        if search_type == 'author':
            return store_books_by_author(query)
        else:
            return store_books_by_title(query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['search_type'] = self.request.GET.get('type', 'title')
        return context

class SignUpView(generic.CreateView):
    form_class = CustomUserCreateForm
    template_name = "signup.html"
    success_url = reverse_lazy("login")

class PublicProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = "public_profile.html"
    slug_field = "username"  # Use username in URL
    slug_url_kwarg = "username"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # favorite books for the profile user
        context['favorite_books'] = self.object.favorite_books.all()
        return context

class ProfileUpdateView(LoginRequiredMixin, generic.UpdateView):
    form_class = CustomUserChangeForm
    template_name = 'profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        # Redirect to /profile/<username> after adding a favorite
        return reverse('public_profile', kwargs={'username': self.request.user.username})

class BookListView(generic.ListView):
    model = Book
    template_name = "books.html"
    context_object_name = "books"
    paginate_by = 24

class BookDetailView(generic.DetailView):
    model = Book
    template_name = "book.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        book = self.object
        user = self.request.user

        is_in_bookshelf = False
        if user.is_authenticated:
            is_in_bookshelf = Bookshelf.objects.filter(
                user=user,
                book=book
            ).exists()

        context["is_in_bookshelf"] = is_in_bookshelf
        return context

class CategoryListView(generic.ListView):
    model = Category
    template_name = "categories.html"
    context_object_name = "categories"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch all categories, ordered alphabetically
        categories = Category.objects.all().order_by('name')

        # Initialize dictionary
        categories_dict = {}

        for category in categories:
            first_letter = category.name[0].upper()
            if not first_letter.isalpha():
                first_letter = '#'
            categories_dict.setdefault(first_letter, []).append(category)  # store the object, not string

        context['categories_dict'] = dict(sorted(categories_dict.items()))
        return context

class CategoryBookListView(generic.ListView):
    model = Book
    template_name = "category_books.html"
    context_object_name = "books"  # match your template
    paginate_by = 24

    def get_queryset(self):
        category_id = self.kwargs.get('pk')
        return Book.objects.filter(categories__id=category_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('pk')
        context['category'] = Category.objects.get(pk=category_id)
        return context

class PostViewList(generic.ListView):
    model = Post
    template_name = "posts.html"
    context_object_name = "posts"
    paginate_by = 20

class PostDetailList(FormMixin, DetailView):
    model = Post
    template_name = "post.html"
    context_object_name = "post"
    form_class = CommentForm

    # URL to redirect to after successful comment
    def get_success_url(self):
        return reverse("post", kwargs={"pk": self.object.pk})

    # Add extra context: form + comments
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure form is available in context
        if 'form' not in context:
            context['form'] = self.get_form()
        # Add comments using your related_name
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
    model = Post
    template_name = "post_form.html"
    form_class = PostCreateUpdateForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('post', kwargs={'pk': self.object.pk})

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Post
    template_name = "post_form.html"
    form_class = PostCreateUpdateForm

    def get_success_url(self):
        return reverse("post", kwargs={"pk" : self.object.pk})

    def test_func(self):
        return self.get_object().author == self.request.user

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Post
    template_name = "post_delete.html"
    context_object_name = "post"
    success_url = reverse_lazy('posts')

    def test_func(self):
        return self.get_object().author == self.request.user

@login_required
def toggle_like_ajax(request, pk):
    post = Post.objects.get(pk=pk)
    if request.user in post.likes.all():  # field is 'likes'
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'total_likes': post.likes.count()
    })

from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

class BookshelfListView(LoginRequiredMixin, generic.ListView):
    model = Bookshelf
    template_name = "bookshelf.html"
    context_object_name = "bookshelf"
    paginate_by = 20

    def get_queryset(self):
        # Return only the bookshelves belonging to the logged-in user
        return Bookshelf.objects.filter(user=self.request.user)

class BookshelfDetailView(LoginRequiredMixin, generic.DetailView):
    model = Bookshelf
    template_name = "bookshelf_book.html"
    context_object_name = "bookshelf_book"

    def get_queryset(self):
        # Optional but recommended: user can only view their own entry
        return Bookshelf.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse("bookshelf")

class BookshelfCreateView(LoginRequiredMixin, generic.CreateView):
    model = Bookshelf
    template_name = "bookshelf_form.html"
    form_class = BookshelfCreateUpdateForm
    success_url = reverse_lazy('bookshelf')

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            # Attempt to save normally
            return super().form_valid(form)
        except IntegrityError:
            # Catch duplicate user/book
            messages.warning(self.request, "You already added this book to your bookshelf.")
            return redirect('bookshelf')



class AddToBookshelfView(LoginRequiredMixin, generic.View):

    def post(self, request, pk):
        book = Book.objects.get(pk=pk)

        Bookshelf.objects.get_or_create(
            user=request.user,
            book=book
        )

        return redirect("book", pk=pk)

class BookshelfUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Bookshelf
    template_name = "bookshelf_form.html"
    form_class = BookshelfCreateUpdateForm

    def get_success_url(self):
        return reverse("bookshelf")

    def test_func(self):
        return self.get_object().user == self.request.user

class BookshelfDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
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
    model = CustomUser
    form_class = FavoriteUpdateForm
    template_name = "add_favorite.html"

    def get_object(self, queryset=None):
        return self.request.user  # edit the logged-in user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # pass user to form
        return kwargs

    def get_success_url(self):
        # Redirect to /profile/<username> after adding a favorite
        return reverse('public_profile', kwargs={'username': self.request.user.username})
