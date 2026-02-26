document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault();
            const postId = btn.dataset.postId;

            fetch(`/posts/${postId}/like-ajax/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                btn.querySelector('.like-count').textContent = data.total_likes;
                btn.innerHTML = (data.liked ? '❤️' : '🤍') + ` <span class="like-count">${data.total_likes}</span>`;
            })
            .catch(err => console.log(err));
        });
    });
});

// Function to get CSRF token from cookie
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}