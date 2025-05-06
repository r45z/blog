// Main JavaScript file for the blog

// Helper function for debouncing functions
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Initialize UI elements when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Highlight current navigation item
    highlightCurrentNav();
    
    // Set up infinite scroll if we're on the posts page
    if (document.getElementById('posts-container')) {
        setupInfiniteScroll();
    }
    
    // Set up newsletter form handling
    const form = document.getElementById('newsletter-form');
    if (form) {
        setupNewsletterForm(form);
    }
});

// Highlight the current navigation link
function highlightCurrentNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentPath === linkPath || 
            (currentPath.startsWith(linkPath) && linkPath !== '/' && linkPath !== '/posts')) {
            link.classList.add('text-white', 'font-semibold');
        }
    });
}

// Set up infinite scroll for posts page
function setupInfiniteScroll() {
    let currentOffset = document.querySelectorAll('.post-item').length;
    let isLoading = false;
    let hasMorePosts = true;
    
    // Function to check if scrolled near bottom
    function isNearBottom() {
        return window.innerHeight + window.scrollY >= document.body.offsetHeight - 500;
    }
    
    // Function to load more posts
    async function loadMorePosts() {
        if (isLoading || !hasMorePosts) return;
        
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.classList.remove('hidden');
        isLoading = true;
        
        try {
            const response = await fetch(`/load_posts?offset=${currentOffset}&limit=5`);
            const data = await response.json();
            
            if (data.posts.length > 0) {
                const postsContainer = document.getElementById('posts-container');
                
                data.posts.forEach(post => {
                    const postElement = document.createElement('article');
                    postElement.className = 'post-item border-b border-gray-800 pb-4';
                    
                    // Extract filename from post's file field
                    const postSlug = post.file ? post.file.replace('.md', '') : '';
                    
                    postElement.innerHTML = `
                        <h2 class="text-xl font-semibold mb-2">
                            <a href="/post/${postSlug}" class="hover:text-blue-400 transition-colors duration-200">
                                ${post.title}
                            </a>
                        </h2>
                        <p class="text-gray-400 text-sm">${post.date}</p>
                    `;
                    postsContainer.appendChild(postElement);
                });
                
                currentOffset += data.posts.length;
            }
            
            // Check if there are more posts
            if (data.posts.length < 5) {
                hasMorePosts = false;
                document.getElementById('end-of-posts').classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error loading posts:', error);
        } finally {
            isLoading = false;
            loadingIndicator.classList.add('hidden');
        }
    }
    
    // Add scroll event listener with debounce
    window.addEventListener('scroll', debounce(() => {
        if (isNearBottom()) {
            loadMorePosts();
        }
    }, 200));
}

// Set up newsletter subscription form
function setupNewsletterForm(form) {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        const email = form.querySelector('input[name="email"]').value;
        const submitButton = form.querySelector('button[type="submit"]');
        const statusMessage = document.getElementById('subscription-status');
        
        // Disable the button and show loading state
        submitButton.disabled = true;
        submitButton.innerText = 'Subscribing...';
        
        try {
            const response = await fetch('/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `email=${encodeURIComponent(email)}`
            });
            
            const result = await response.json();
            
            if (result.success) {
                statusMessage.innerText = result.message || 'Thank you for subscribing!';
                statusMessage.className = 'text-green-400 mt-2';
                form.reset();
            } else {
                statusMessage.innerText = result.message || 'Subscription failed. Please try again.';
                statusMessage.className = 'text-red-400 mt-2';
            }
        } catch (error) {
            statusMessage.innerText = 'An error occurred. Please try again later.';
            statusMessage.className = 'text-red-400 mt-2';
            console.error('Subscription error:', error);
        } finally {
            submitButton.disabled = false;
            submitButton.innerText = 'Subscribe';
        }
    });
} 