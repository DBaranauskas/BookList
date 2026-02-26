import requests
from django.conf import settings
from .models import Book, Author, Category


def search_books_by_title(user_query, max_results=20):
    query = f"intitle:{user_query.replace(' ', '+')}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={max_results}&key={settings.GOOGLE_BOOKS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return []

    results = response.json().get('items', [])
    books = []
    duplicates = []

    for item in results:
        volume_info = item.get('volumeInfo', {})
        lang = volume_info.get('language', '').lower()
        if not lang.startswith('en'):
            continue

        title = volume_info.get('title', '').strip()
        authors_list = [a.strip() for a in volume_info.get('authors', []) if a.strip()]
        description = volume_info.get('description', '').strip()
        thumbnail = volume_info.get('imageLinks', {}).get('thumbnail', '')
        categories = volume_info.get('categories', [])

        # Skip books missing authors, description, thumbnail, or categories
        if not authors_list or not description or not thumbnail or not categories:
            continue

        # Skip duplicates
        key = (title.lower(), ", ".join(authors_list).lower())
        if key in duplicates:
            continue
        duplicates.append(key)

        isbn_10 = None
        isbn_13 = None
        for iden in volume_info.get('industryIdentifiers', []):
            if iden.get('type') == 'ISBN_10':
                isbn_10 = iden.get('identifier')
            elif iden.get('type') == 'ISBN_13':
                isbn_13 = iden.get('identifier')

        published_date = volume_info.get('publishedDate', '').strip()

        books.append({
            'google_books_id': item.get('id'),
            'title': title,
            'authors': ', '.join(authors_list),
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'isbn_10': isbn_10,
            'isbn_13': isbn_13,
            'published_date': published_date,
        })

    return books


def store_books_by_title(query, max_results=10):
    results = search_books_by_title(query, max_results)

    for item in results:
        google_id = item.get('google_books_id')
        if not google_id:
            continue

        # Skip if thumbnail or categories are missing (extra safety)
        thumbnail = item.get('thumbnail')
        categories = item.get('categories', [])
        if not thumbnail or not categories:
            continue

        # Skip if already in DB
        book_obj, created = Book.objects.get_or_create(
            google_books_id=google_id,
            defaults={
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'isbn_13': item.get('isbn_13', ''),
                'isbn_10': item.get('isbn_10', ''),
                'release_date': item.get('published_date', '')
            }
        )

        # Add cover URL if available
        if thumbnail and not book_obj.thumbnail:
            book_obj.thumbnail = thumbnail.replace("http://", "https://")
            book_obj.save(update_fields=["thumbnail"])

        # Add authors
        authors_list = item.get('authors', '').split(', ')
        for author_name in authors_list:
            author_name = author_name.strip()
            if author_name:
                author_obj, _ = Author.objects.get_or_create(full_name=author_name)
                book_obj.authors.add(author_obj)

        # Add categories
        for category in categories:
            for part in category.split("/"):
                category_name = part.strip()
                if category_name:
                    category_obj, _ = Category.objects.get_or_create(name=category_name)
                    book_obj.categories.add(category_obj)

    return Book.objects.filter(title__icontains=query)

def search_books_by_author(author_name, max_results=20):
    query = f"inauthor:{author_name.replace(' ', '+')}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={max_results}&key={settings.GOOGLE_BOOKS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return []

    results = response.json().get('items', [])
    books = []
    duplicates = []

    for item in results:
        volume_info = item.get('volumeInfo', {})
        lang = volume_info.get('language', '').lower()
        if not lang.startswith('en'):
            continue

        title = volume_info.get('title', '').strip()
        authors_list = [a.strip() for a in volume_info.get('authors', []) if a.strip()]
        description = volume_info.get('description', '').strip()
        thumbnail = volume_info.get('imageLinks', {}).get('thumbnail', '')
        categories = volume_info.get('categories', [])

        # Skip books missing authors, description, thumbnail, or categories
        if not authors_list or not description or not thumbnail or not categories:
            continue

        # Skip duplicates
        key = (title.lower(), ", ".join(authors_list).lower())
        if key in duplicates:
            continue
        duplicates.append(key)

        isbn_10 = None
        isbn_13 = None
        for iden in volume_info.get('industryIdentifiers', []):
            if iden.get('type') == 'ISBN_10':
                isbn_10 = iden.get('identifier')
            elif iden.get('type') == 'ISBN_13':
                isbn_13 = iden.get('identifier')

        published_date = volume_info.get('publishedDate', '').strip()

        books.append({
            'google_books_id': item.get('id'),
            'title': title,
            'authors': ', '.join(authors_list),
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'isbn_10': isbn_10,
            'isbn_13': isbn_13,
            'published_date': published_date,
        })

    return books


def store_books_by_author(author_name, max_results=10):
    results = search_books_by_author(author_name, max_results)

    for item in results:
        google_id = item.get('google_books_id')
        if not google_id:
            continue

        thumbnail = item.get('thumbnail')
        categories = item.get('categories', [])
        if not thumbnail or not categories:
            continue

        # Skip if already in DB
        book_obj, created = Book.objects.get_or_create(
            google_books_id=google_id,
            defaults={
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'isbn_13': item.get('isbn_13', ''),
                'isbn_10': item.get('isbn_10', ''),
                'release_date': item.get('published_date', '')
            }
        )

        if thumbnail and not book_obj.thumbnail:
            book_obj.thumbnail = thumbnail.replace("http://", "https://")
            book_obj.save(update_fields=["thumbnail"])

        # Add authors
        authors_list = item.get('authors', '').split(', ')
        for author in authors_list:
            author = author.strip()
            if author:
                author_obj, _ = Author.objects.get_or_create(full_name=author)
                book_obj.authors.add(author_obj)

        # Add categories
        for category in categories:
            for part in category.split("/"):
                category_name = part.strip()
                if category_name:
                    category_obj, _ = Category.objects.get_or_create(name=category_name)
                    book_obj.categories.add(category_obj)

    return Book.objects.filter(authors__full_name__icontains=author_name)