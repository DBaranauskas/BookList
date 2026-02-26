from django.urls import path, include
from . import views

urlpatterns = [
    path('about', views.about_page, name="about"),
    path('search/', views.BookSearchListView.as_view(), name='book_search'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', views.CategoryBookListView.as_view(), name='category_book'),
    path('', views.PostViewList.as_view(), name="posts" ),
    path('posts/<int:pk>/', views.PostDetailList.as_view(), name="post"),
    path('posts/create', views.PostCreateView.as_view(), name="post_create"),
    path('posts/<int:pk>/update/', views.PostUpdateView.as_view(), name="post_update"),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name="post_delete"),
    path('posts/<int:pk>/like-ajax/', views.toggle_like_ajax, name="post_like_ajax"),
    path('bookshelf/', views.BookshelfListView.as_view(), name="bookshelf"),
    path('bookshelf/<int:pk>', views.BookshelfDetailView.as_view(), name="bookshelf_book"),
    path('bookshelf/create', views.BookshelfCreateView.as_view(), name="bookshelf_create"),
    path("book/<int:pk>/add/", views.AddToBookshelfView.as_view(), name="add_to_bookshelf"),
    path('bookshelf/<int:pk>/update/', views.BookshelfUpdateView.as_view(), name="bookshelf_update"),
    path('bookshelf/<int:pk>/delete/', views.BookshelfDeleteView.as_view(), name="bookshelf_delete"),
    path('profile/favorite/add', views.FavoriteUpdateView.as_view(), name="favorite_add"),
]