/**
 * Vue 3 SPA with Vue Router 4
 * CinemaBook Single Page Application
 */
const { createApp } = Vue;
const { createRouter, createWebHistory } = VueRouter;

// === Shared Utilities ===

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 4000);
}

function starsDisplay(rating) {
    return '⭐'.repeat(Math.round(rating));
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('uk-UA', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function formatDateShort(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('uk-UA', {
        day: '2-digit', month: '2-digit', year: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString.replace(' ', 'T'));
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleString('uk-UA', {
        day: 'numeric', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

// === Auth State ===
const authState = {
    authenticated: false,
    user: null,

    async check() {
        try {
            const res = await fetch('/api/auth/status');
            const data = await res.json();
            this.authenticated = data.authenticated;
            this.user = data.user;
        } catch (e) {
            this.authenticated = false;
            this.user = null;
        }
        this.updateNavbar();
        return this.authenticated;
    },

    setUser(user) {
        this.authenticated = true;
        this.user = user;
        this.updateNavbar();
    },

    clear() {
        this.authenticated = false;
        this.user = null;
        this.updateNavbar();
    },

    updateNavbar() {
        document.querySelectorAll('.spa-auth-only').forEach(el => {
            el.style.display = this.authenticated ? '' : 'none';
        });
        document.querySelectorAll('.spa-guest-only').forEach(el => {
            el.style.display = this.authenticated ? 'none' : '';
        });
        document.querySelectorAll('.spa-admin-only').forEach(el => {
            el.style.display = (this.authenticated && this.user?.is_admin) ? '' : 'none';
        });
    }
};


// ===========================
// === Films Page Component ===
// ===========================
const FilmsPage = {
    template: '#films-template',
    data() {
        return {
            films: [],
            genres: [],
            searchQuery: '',
            selectedGenre: '',
            loading: true,
            error: null,
            searchTimeout: null
        };
    },
    computed: {
        resultsText() {
            const count = this.films.length;
            if (count === 0) return 'Нічого не знайдено';
            if (count === 1) return '1 фільм';
            if (count < 5) return `${count} фільми`;
            return `${count} фільмів`;
        }
    },
    watch: {
        searchQuery() {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => this.fetchFilms(), 300);
        },
        selectedGenre() {
            this.fetchFilms();
        }
    },
    methods: {
        async fetchFilms() {
            try {
                this.loading = true;
                const params = new URLSearchParams();
                if (this.searchQuery) params.set('q', this.searchQuery);
                if (this.selectedGenre) params.set('genre', this.selectedGenre);

                const response = await fetch(`/api/films?${params}`);
                const data = await response.json();
                this.films = data.films;
                if (data.genres && data.genres.length > 0) {
                    this.genres = data.genres;
                }
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        clearFilters() {
            this.searchQuery = '';
            this.selectedGenre = '';
        },
        goToFilm(filmId) {
            this.$router.push({ name: 'film-detail', params: { id: filmId } });
        },
        async toggleFavorite(film, event) {
            event.stopPropagation();
            try {
                const method = film.is_favorite ? 'DELETE' : 'POST';
                const response = await fetch(`/api/favorites/${film.id}`, { method });
                const data = await response.json();
                if (data.success) {
                    film.is_favorite = data.action === 'added';
                }
            } catch (err) {
                console.error('Favorite toggle error:', err);
            }
        },
        starsDisplay,
        truncate(text, length) {
            if (!text) return 'Опис відсутній.';
            return text.length > length ? text.substring(0, length) + '...' : text;
        }
    },
    mounted() {
        const params = new URLSearchParams(window.location.search);
        this.searchQuery = params.get('q') || '';
        this.selectedGenre = params.get('genre') || '';
        this.fetchFilms();
    }
};


// =================================
// === Film Detail Page Component ===
// =================================
const FilmDetailPage = {
    template: '#film-detail-template',
    data() {
        return {
            filmId: null,
            film: null,
            sessions: [],
            reviews: [],
            similarFilms: [],
            userReview: null,
            isAuthenticated: false,
            currentUserId: null,
            isAdmin: false,
            reviewForm: { rating: 5, comment: '' },
            submittingReview: false,
            loading: true,
            error: null
        };
    },
    computed: {
        canReview() {
            return this.isAuthenticated && !this.userReview;
        },
        ratingStars() {
            if (!this.film) return '';
            return starsDisplay(this.film.average_rating);
        }
    },
    watch: {
        '$route.params.id'(newId) {
            if (newId) {
                this.filmId = newId;
                this.loading = true;
                this.loadFilm();
            }
        }
    },
    methods: {
        async loadFilm() {
            try {
                this.loading = true;
                const response = await fetch(`/api/films/${this.filmId}`);
                if (!response.ok) throw new Error('Фільм не знайдено');
                const data = await response.json();
                this.film = data.film;
                this.sessions = data.sessions;
                this.reviews = data.reviews;
                this.userReview = data.user_review;
                this.similarFilms = data.similar_films;
                this.isAuthenticated = data.is_authenticated;
                this.currentUserId = data.current_user_id;
                this.isAdmin = data.is_admin;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        async toggleFavorite() {
            if (!this.isAuthenticated) {
                this.$router.push('/login');
                return;
            }
            try {
                const method = this.film.is_favorite ? 'DELETE' : 'POST';
                const response = await fetch(`/api/favorites/${this.film.id}`, { method });
                const data = await response.json();
                if (data.success) {
                    this.film.is_favorite = data.action === 'added';
                }
            } catch (err) {
                console.error('Favorite error:', err);
            }
        },
        async submitReview() {
            if (this.submittingReview) return;
            this.submittingReview = true;
            try {
                const response = await fetch(`/api/films/${this.filmId}/reviews`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.reviewForm)
                });
                const data = await response.json();
                if (!response.ok) {
                    showAlert(data.error, 'danger');
                    return;
                }
                this.reviews.unshift(data.review);
                this.userReview = { id: data.review.id, rating: data.review.rating, comment: data.review.comment };
                this.film.average_rating = data.new_average_rating;
                this.film.review_count = this.reviews.length;
                this.reviewForm = { rating: 5, comment: '' };
                showAlert('Відгук опубліковано!', 'success');
            } catch (err) {
                showAlert('Помилка при відправці відгуку', 'danger');
            } finally {
                this.submittingReview = false;
            }
        },
        async deleteReview(reviewId) {
            if (!confirm('Ви впевнені?')) return;
            try {
                const response = await fetch(`/api/reviews/${reviewId}`, { method: 'DELETE' });
                const data = await response.json();
                if (data.success) {
                    this.reviews = this.reviews.filter(r => r.id !== reviewId);
                    this.film.average_rating = data.new_average_rating;
                    this.film.review_count = this.reviews.length;
                    if (this.userReview && this.userReview.id === reviewId) {
                        this.userReview = null;
                    }
                    showAlert('Відгук видалено', 'success');
                }
            } catch (err) {
                showAlert('Помилка при видаленні', 'danger');
            }
        },
        canDeleteReview(review) {
            return this.currentUserId === review.user_id || this.isAdmin;
        },
        formatDate,
        starsDisplay,
        getEmbedUrl(trailerUrl) {
            if (!trailerUrl) return '';
            return trailerUrl.replace('watch?v=', 'embed/');
        },
        goToSimilar(filmId) {
            this.$router.push({ name: 'film-detail', params: { id: filmId } });
        }
    },
    mounted() {
        this.filmId = this.$route.params.id;
        if (this.filmId) {
            this.loadFilm();
        }
    }
};


// ==============================
// === Profile Page Component ===
// ==============================
const ProfilePage = {
    template: '#profile-template',
    data() {
        return {
            user: null,
            bookings: [],
            filter: 'active',
            loading: true,
            error: null
        };
    },
    computed: {
        activeBookings() {
            return this.bookings.filter(b => !b.is_cancelled);
        },
        cancelledBookings() {
            return this.bookings.filter(b => b.is_cancelled);
        },
        filteredBookings() {
            if (this.filter === 'active') return this.activeBookings;
            if (this.filter === 'cancelled') return this.cancelledBookings;
            return this.bookings;
        },
        totalSpent() {
            return this.activeBookings.reduce((sum, b) => sum + b.price, 0).toFixed(0);
        }
    },
    methods: {
        async loadProfile() {
            try {
                this.loading = true;
                const response = await fetch('/api/user/profile');
                if (!response.ok) throw new Error('Помилка завантаження');
                const data = await response.json();
                this.user = data.user;
                this.bookings = data.bookings;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        async cancelBooking(bookingId) {
            if (!confirm('Ви впевнені, що хочете скасувати бронювання?')) return;
            try {
                const response = await fetch(`/api/bookings/${bookingId}/cancel`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    const booking = this.bookings.find(b => b.id === bookingId);
                    if (booking) booking.is_cancelled = true;
                    showAlert('Бронювання скасовано', 'success');
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (err) {
                showAlert('Помилка скасування', 'danger');
            }
        },
        setFilter(type) {
            this.filter = type;
        },
        goToFilm(filmId) {
            this.$router.push({ name: 'film-detail', params: { id: filmId } });
        }
    },
    mounted() {
        this.loadProfile();
    }
};


// ================================
// === Favorites Page Component ===
// ================================
const FavoritesPage = {
    template: '#favorites-template',
    data() {
        return {
            favorites: [],
            loading: true,
            error: null
        };
    },
    methods: {
        async loadFavorites() {
            try {
                this.loading = true;
                const response = await fetch('/api/favorites');
                if (!response.ok) throw new Error('Помилка завантаження');
                const data = await response.json();
                this.favorites = data.favorites;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        async removeFavorite(filmId) {
            if (!confirm('Видалити з обраних?')) return;
            try {
                const response = await fetch(`/api/favorites/${filmId}`, { method: 'DELETE' });
                const data = await response.json();
                if (data.success) {
                    this.favorites = this.favorites.filter(f => f.id != filmId);
                    showAlert('Видалено з обраних', 'success');
                }
            } catch (err) {
                showAlert('Помилка видалення', 'danger');
            }
        },
        goToFilm(filmId) {
            this.$router.push({ name: 'film-detail', params: { id: filmId } });
        },
        formatDate: formatDateShort,
        starsDisplay
    },
    mounted() {
        this.loadFavorites();
    }
};


// ============================
// === Login Page Component ===
// ============================
const LoginPage = {
    template: '#login-template',
    data() {
        return {
            email: '',
            password: '',
            errors: {},
            generalError: '',
            submitting: false
        };
    },
    methods: {
        async submitLogin() {
            this.errors = {};
            this.generalError = '';

            if (!this.email.trim()) this.errors.email = 'Введіть email';
            if (!this.password) this.errors.password = 'Введіть пароль';
            if (Object.keys(this.errors).length) return;

            this.submitting = true;
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: this.email.trim(), password: this.password })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    authState.setUser(data.user);
                    showAlert(data.message, 'success');
                    const next = this.$route.query.next || '/films';
                    this.$router.push(next);
                } else {
                    this.generalError = data.error || 'Помилка входу';
                }
            } catch (e) {
                this.generalError = 'Помилка з\'єднання з сервером';
            } finally {
                this.submitting = false;
            }
        }
    }
};


// ===============================
// === Register Page Component ===
// ===============================
const RegisterPage = {
    template: '#register-template',
    data() {
        return {
            name: '',
            email: '',
            password: '',
            errors: {},
            generalError: '',
            submitting: false
        };
    },
    methods: {
        async submitRegister() {
            this.errors = {};
            this.generalError = '';

            if (!this.name.trim() || this.name.trim().length < 2) {
                this.errors.name = "Ім'я має бути мінімум 2 символи";
            }
            if (!this.email.trim()) this.errors.email = 'Введіть email';
            if (!this.password || this.password.length < 6) {
                this.errors.password = 'Пароль має бути мінімум 6 символів';
            }
            if (Object.keys(this.errors).length) return;

            this.submitting = true;
            try {
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.name.trim(),
                        email: this.email.trim(),
                        password: this.password
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    authState.setUser(data.user);
                    showAlert(data.message, 'success');
                    this.$router.push('/films');
                } else if (data.errors) {
                    this.errors = data.errors;
                } else {
                    this.generalError = data.error || 'Помилка реєстрації';
                }
            } catch (e) {
                this.generalError = 'Помилка з\'єднання з сервером';
            } finally {
                this.submitting = false;
            }
        }
    }
};


// ============================
// === Seats Page Component ===
// ============================
const SeatsPage = {
    template: '#seats-template',
    data() {
        return {
            sessionId: null,
            session: null,
            seats: [],
            selectedSeats: [],
            userBookings: { count: 0, remaining_slots: 5 },
            loading: true,
            error: null,
            booking: false
        };
    },
    computed: {
        seatsByRow() {
            const grouped = {};
            this.seats.forEach(seat => {
                if (!grouped[seat.row]) grouped[seat.row] = [];
                grouped[seat.row].push(seat);
            });
            return Object.keys(grouped)
                .sort((a, b) => parseInt(a) - parseInt(b))
                .reduce((acc, row) => {
                    acc[row] = grouped[row].sort((a, b) => a.number - b.number);
                    return acc;
                }, {});
        },
        totalPrice() {
            return this.selectedSeats.length * (this.session?.price || 0);
        },
        canSelectMore() {
            return this.selectedSeats.length + this.userBookings.count < 5;
        },
        hasSelection() {
            return this.selectedSeats.length > 0;
        }
    },
    methods: {
        async loadSeats() {
            try {
                this.loading = true;
                this.error = null;
                const response = await fetch(`/api/sessions/${this.sessionId}/seats`);
                if (!response.ok) throw new Error('Помилка завантаження даних');
                const data = await response.json();
                this.session = data.session;
                this.seats = data.seats;
                this.userBookings = data.user_bookings;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        toggleSeat(seat) {
            if (seat.status === 'booked') return;
            const index = this.selectedSeats.indexOf(seat.id);
            if (index > -1) {
                this.selectedSeats.splice(index, 1);
            } else {
                if (this.canSelectMore) {
                    this.selectedSeats.push(seat.id);
                } else {
                    showAlert('Максимум 5 місць на один сеанс!', 'warning');
                }
            }
        },
        isSeatSelected(seat) {
            return this.selectedSeats.includes(seat.id);
        },
        getSeatClass(seat) {
            if (seat.status === 'booked') return 'booked';
            if (this.isSeatSelected(seat)) return 'selected';
            return 'free';
        },
        async bookSeats() {
            if (!this.hasSelection) {
                showAlert('Оберіть хоча б одне місце', 'warning');
                return;
            }
            try {
                this.booking = true;
                const response = await fetch(`/api/sessions/${this.sessionId}/book`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ seat_ids: this.selectedSeats })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Помилка бронювання');
                showAlert(data.message, 'success');
                setTimeout(() => {
                    this.$router.push({ name: 'profile' });
                }, 2000);
            } catch (err) {
                showAlert(err.message, 'danger');
            } finally {
                this.booking = false;
            }
        },
        formatDateTime
    },
    mounted() {
        this.sessionId = this.$route.params.sessionId;
        if (this.sessionId) {
            this.loadSeats();
        } else {
            this.error = 'Session ID не знайдено';
        }
    }
};


// =============================
// === Landing Page Component ===
// =============================
const LandingPage = {
    template: '#landing-template',
    data() {
        return {
            popularFilms: [],
            loading: true,
            error: null
        };
    },
    methods: {
        async loadPopularFilms() {
            try {
                this.loading = true;
                const res = await fetch('/api/films/popular');
                if (!res.ok) throw new Error('Помилка завантаження');
                const data = await res.json();
                this.popularFilms = data.films || [];
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        goToFilm(filmId) {
            this.$router.push({ name: 'film-detail', params: { id: filmId } });
        },
        scrollToFeatures() {
            const features = document.getElementById('features');
            if (features) {
                features.scrollIntoView({ behavior: 'smooth' });
            }
        },
        starsDisplay(rating) {
            return '⭐'.repeat(Math.round(rating));
        },
        async toggleFavorite(film) {
            if (!authState.authenticated) {
                this.$router.push({ name: 'login' });
                return;
            }
            try {
                const res = await fetch(`/api/favorites/${film.id}/toggle`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    film.is_favorited = data.is_favorited;
                    showAlert(data.message, 'success');
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (e) {
                showAlert('Помилка з\'єднання', 'danger');
            }
        }
    },
    mounted() {
        this.loadPopularFilms();
    }
};


// ==========================================
// === Admin Dashboard Page Component ===
// ==========================================
const AdminDashboardPage = {
    template: '#admin-dashboard-template',
    data() {
        return {
            stats: null,
            loading: true,
            error: null
        };
    },
    methods: {
        async loadStats() {
            try {
                this.loading = true;
                const res = await fetch('/api/admin/stats');
                if (!res.ok) throw new Error('Помилка завантаження');
                this.stats = await res.json();
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        }
    },
    mounted() {
        this.loadStats();
    }
};


// =====================================
// === Admin Films Page Component ===
// =====================================
const AdminFilmsPage = {
    template: '#admin-films-template',
    data() {
        return {
            films: [],
            loading: true,
            error: null,
            showForm: false,
            editingFilm: null,
            form: this.emptyForm(),
            submitting: false,
            formError: ''
        };
    },
    methods: {
        emptyForm() {
            return {
                title: '', description: '', genre: '', director: '', actors: '',
                duration: '', age_rating: '', release_year: '', trailer: '', image: null
            };
        },
        async loadFilms() {
            try {
                this.loading = true;
                const res = await fetch('/api/admin/films');
                if (!res.ok) throw new Error('Помилка завантаження');
                const data = await res.json();
                this.films = data.films;
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        openAddForm() {
            this.editingFilm = null;
            this.form = this.emptyForm();
            this.formError = '';
            this.showForm = true;
        },
        openEditForm(film) {
            this.editingFilm = film;
            this.form = {
                title: film.title || '',
                description: film.description || '',
                genre: film.genre || '',
                director: film.director || '',
                actors: film.actors || '',
                duration: film.duration || '',
                age_rating: film.age_rating || '',
                release_year: film.release_year || '',
                trailer: film.trailer || '',
                image: null
            };
            this.formError = '';
            this.showForm = true;
        },
        cancelForm() {
            this.showForm = false;
            this.editingFilm = null;
        },
        onFileChange(e) {
            this.form.image = e.target.files[0] || null;
        },
        async submitForm() {
            this.formError = '';
            if (!this.form.title.trim()) { this.formError = 'Назва обов\'язкова'; return; }
            if (!this.form.description.trim() || this.form.description.trim().length < 10) {
                this.formError = 'Опис мінімум 10 символів'; return;
            }

            this.submitting = true;
            try {
                const fd = new FormData();
                for (const [key, val] of Object.entries(this.form)) {
                    if (key === 'image') {
                        if (val) fd.append('image', val);
                    } else {
                        fd.append(key, val ?? '');
                    }
                }

                const url = this.editingFilm
                    ? `/api/admin/films/${this.editingFilm.id}`
                    : '/api/admin/films';
                const method = this.editingFilm ? 'PUT' : 'POST';

                const res = await fetch(url, { method, body: fd });
                const data = await res.json();
                if (!res.ok) { this.formError = data.error || 'Помилка'; return; }

                showAlert(data.message, 'success');
                this.showForm = false;
                this.editingFilm = null;
                await this.loadFilms();
            } catch (e) {
                this.formError = 'Помилка з\'єднання';
            } finally {
                this.submitting = false;
            }
        },
        async deleteFilm(film) {
            if (!confirm(`Видалити фільм «${film.title}»?`)) return;
            try {
                const res = await fetch(`/api/admin/films/${film.id}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    this.films = this.films.filter(f => f.id !== film.id);
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (e) {
                showAlert('Помилка видалення', 'danger');
            }
        },
        truncate(text, len) {
            if (!text) return '';
            return text.length > len ? text.substring(0, len) + '...' : text;
        }
    },
    mounted() {
        this.loadFilms();
    }
};


// ========================================
// === Admin Sessions Page Component ===
// ========================================
const AdminSessionsPage = {
    template: '#admin-sessions-template',
    data() {
        return {
            sessions: [],
            films: [],
            loading: true,
            error: null,
            showForm: false,
            form: { film_id: '', start_time: '', price: '' },
            submitting: false,
            formError: '',
            filter: 'all'
        };
    },
    computed: {
        filteredSessions() {
            if (this.filter === 'active') return this.sessions.filter(s => s.status === 'active');
            if (this.filter === 'cancelled') return this.sessions.filter(s => s.status === 'cancelled');
            return this.sessions;
        },
        activeSessions() { return this.sessions.filter(s => s.status === 'active'); },
        cancelledSessions() { return this.sessions.filter(s => s.status === 'cancelled'); }
    },
    methods: {
        async loadData() {
            try {
                this.loading = true;
                const [sessRes, filmsRes] = await Promise.all([
                    fetch('/api/admin/sessions'),
                    fetch('/api/admin/films')
                ]);
                if (!sessRes.ok || !filmsRes.ok) throw new Error('Помилка завантаження');
                const sessData = await sessRes.json();
                const filmsData = await filmsRes.json();
                this.sessions = sessData.sessions;
                this.films = filmsData.films;
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        openForm() {
            this.form = { film_id: '', start_time: '', price: '' };
            this.formError = '';
            this.showForm = true;
        },
        async submitForm() {
            this.formError = '';
            if (!this.form.film_id || !this.form.start_time || !this.form.price) {
                this.formError = 'Заповніть всі поля'; return;
            }
            this.submitting = true;
            try {
                const payload = {
                    film_id: parseInt(this.form.film_id),
                    start_time: this.form.start_time.replace('T', ' '),
                    price: parseFloat(this.form.price)
                };
                const res = await fetch('/api/admin/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });
                const data = await res.json();
                if (!res.ok) { this.formError = data.error || 'Помилка'; return; }
                showAlert(data.message, 'success');
                this.showForm = false;
                await this.loadData();
            } catch (e) {
                this.formError = 'Помилка з\'єднання';
            } finally {
                this.submitting = false;
            }
        },
        async cancelSession(session) {
            if (!confirm(`Скасувати сеанс "${session.film_title}" (${session.start_time})?`)) return;
            try {
                const res = await fetch(`/api/admin/sessions/${session.id}/cancel`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    session.status = 'cancelled';
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (e) {
                showAlert('Помилка скасування', 'danger');
            }
        },
        formatDateTime
    },
    mounted() {
        this.loadData();
    }
};


// =====================================
// === Admin Calendar Page Component ===
// =====================================
const AdminCalendarPage = {
    template: '#admin-calendar-template',
    data() {
        return {
            weekDays: [],
            timeSlots: [],
            sessionsGrid: {},
            films: [],
            weekOffset: 0,
            startOfWeek: '',
            loading: true,
            error: null,
            showModal: false,
            modalData: {
                date: '',
                dateDisplay: '',
                time: ''
            },
            createForm: {
                film_id: '',
                price: 150
            },
            submitting: false
        };
    },
    methods: {
        async loadCalendar() {
            try {
                this.loading = true;
                const res = await fetch(`/api/admin/calendar?week=${this.weekOffset}`);
                if (!res.ok) throw new Error('Помилка завантаження');
                const data = await res.json();
                this.weekDays = data.week_days;
                this.timeSlots = data.time_slots;
                this.sessionsGrid = data.sessions_grid;
                this.films = data.films;
                this.startOfWeek = data.start_of_week;
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        prevWeek() {
            this.weekOffset--;
            this.loadCalendar();
        },
        nextWeek() {
            this.weekOffset++;
            this.loadCalendar();
        },
        currentWeek() {
            this.weekOffset = 0;
            this.loadCalendar();
        },
        getSessionsForSlot(date, time) {
            const key = `${date}#${time}`;
            return this.sessionsGrid[key] || [];
        },
        openCreateModal(date, time) {
            const dateObj = new Date(date);
            this.modalData.date = date;
            this.modalData.dateDisplay = dateObj.toLocaleDateString('uk-UA', {
                day: '2-digit', month: '2-digit', year: 'numeric'
            });
            this.modalData.time = time;
            this.createForm.film_id = '';
            this.createForm.price = 150;
            this.showModal = true;
        },
        async createSession() {
            if (!this.createForm.film_id || !this.createForm.price) {
                showAlert('Заповніть всі поля', 'danger');
                return;
            }
            this.submitting = true;
            try {
                const res = await fetch('/api/admin/calendar/create-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        film_id: parseInt(this.createForm.film_id),
                        date: this.modalData.date,
                        time: this.modalData.time,
                        price: parseFloat(this.createForm.price)
                    })
                });
                const data = await res.json();
                if (!res.ok) {
                    showAlert(data.error || 'Помилка створення', 'danger');
                    return;
                }
                showAlert(data.message, 'success');
                this.showModal = false;
                await this.loadCalendar();
            } catch (e) {
                showAlert('Помилка з\'єднання', 'danger');
            } finally {
                this.submitting = false;
            }
        },
        async cancelSession(sessionId, event) {
            if (event) event.stopPropagation();
            if (!confirm('Ви впевнені, що хочете скасувати цей сеанс?')) return;
            try {
                const res = await fetch(`/api/admin/sessions/${sessionId}/cancel`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    await this.loadCalendar();
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (e) {
                showAlert('Помилка скасування', 'danger');
            }
        },
        weekLabel() {
            if (this.weekOffset === 0) return '📅 Поточний тиждень';
            if (this.weekOffset === 1) return '📅 Наступний тиждень';
            if (this.weekOffset > 1) return `📅 +${this.weekOffset} тижнів`;
            return `📅 ${this.weekOffset} тижнів назад`;
        },
        weekRange() {
            if (!this.startOfWeek) return '';
            const start = new Date(this.startOfWeek);
            const end = new Date(start);
            end.setDate(end.getDate() + 6);
            return `${start.toLocaleDateString('uk-UA')} - ${end.toLocaleDateString('uk-UA')}`;
        }
    },
    mounted() {
        this.loadCalendar();
    }
};


// ===========================
// === Breadcrumbs Component ===
// ===========================
const Breadcrumbs = {
    template: `
        <div class="breadcrumbs" v-if="items.length > 0">
            <template v-for="(item, index) in items" :key="index">
                <router-link v-if="index < items.length - 1" :to="item.path">
                    <i v-if="item.icon" :class="item.icon"></i> {{ item.label }}
                </router-link>
                <span v-else class="active">
                    <i v-if="item.icon" :class="item.icon"></i> {{ item.label }}
                </span>
                <span v-if="index < items.length - 1"> / </span>
            </template>
        </div>
    `,
    computed: {
        items() {
            const route = this.$route;
            const items = [{ label: 'Головна', path: '/', icon: 'fas fa-home' }];
            
            if (route.name === 'landing') return [];
            if (route.name === 'films') {
                items.push({ label: 'Фільми', path: '/films', icon: 'fas fa-film' });
            } else if (route.name === 'film-detail') {
                items.push({ label: 'Фільми', path: '/films', icon: 'fas fa-film' });
                items.push({ label: 'Деталі фільму', path: route.path });
            } else if (route.name === 'favorites') {
                items.push({ label: 'Обрані', path: '/favorites', icon: 'fas fa-heart' });
            } else if (route.name === 'profile') {
                items.push({ label: 'Профіль', path: '/profile', icon: 'fas fa-user' });
            } else if (route.name === 'seats') {
                items.push({ label: 'Фільми', path: '/films', icon: 'fas fa-film' });
                items.push({ label: 'Вибір місць', path: route.path, icon: 'fas fa-couch' });
            } else if (route.name === 'login') {
                items.push({ label: 'Вхід', path: '/login', icon: 'fas fa-sign-in-alt' });
            } else if (route.name === 'register') {
                items.push({ label: 'Реєстрація', path: '/register', icon: 'fas fa-user-plus' });
            } else if (route.name && route.name.startsWith('admin')) {
                items.push({ label: 'Адмін-панель', path: '/admin', icon: 'fas fa-cog' });
                if (route.name === 'admin-films') {
                    items.push({ label: 'Фільми', path: '/admin/films', icon: 'fas fa-film' });
                } else if (route.name === 'admin-sessions') {
                    items.push({ label: 'Сеанси', path: '/admin/sessions', icon: 'fas fa-ticket-alt' });
                } else if (route.name === 'admin-calendar') {
                    items.push({ label: 'Календар', path: '/admin/calendar', icon: 'fas fa-calendar-week' });
                }
            }
            
            return items;
        }
    }
};


// ===========================
// === Back to Top Component ===
// ===========================
const BackToTop = {
    template: `
        <button @click="scrollToTop" class="back-to-top" :class="{ show: isVisible }">
            <i class="fas fa-arrow-up"></i>
        </button>
    `,
    data() {
        return {
            isVisible: false
        };
    },
    methods: {
        scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        handleScroll() {
            this.isVisible = window.scrollY > 300;
        }
    },
    mounted() {
        window.addEventListener('scroll', this.handleScroll);
    },
    beforeUnmount() {
        window.removeEventListener('scroll', this.handleScroll);
    }
};


// ===========================
// === Not Found Page Component ===
// ===========================
const NotFoundPage = {
    template: '#not-found-template',
    methods: {
        goHome() {
            this.$router.push('/');
        },
        goBack() {
            this.$router.go(-1);
        }
    }
};


// ==============================
// === Router Configuration ===
// ==============================
const routes = [
    { path: '/', name: 'landing', component: LandingPage },
    { path: '/films', name: 'films', component: FilmsPage },
    { path: '/film/:id', name: 'film-detail', component: FilmDetailPage },
    { path: '/login', name: 'login', component: LoginPage, meta: { guest: true } },
    { path: '/register', name: 'register', component: RegisterPage, meta: { guest: true } },
    { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresAuth: true } },
    { path: '/favorites', name: 'favorites', component: FavoritesPage, meta: { requiresAuth: true } },
    { path: '/seats/:sessionId', name: 'seats', component: SeatsPage, meta: { requiresAuth: true } },
    { path: '/admin', name: 'admin-dashboard', component: AdminDashboardPage, meta: { requiresAdmin: true } },
    { path: '/admin/films', name: 'admin-films', component: AdminFilmsPage, meta: { requiresAdmin: true } },
    { path: '/admin/sessions', name: 'admin-sessions', component: AdminSessionsPage, meta: { requiresAdmin: true } },
    { path: '/admin/calendar', name: 'admin-calendar', component: AdminCalendarPage, meta: { requiresAdmin: true } },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundPage }
];

const router = createRouter({
    history: createWebHistory('/app'),
    routes,
    scrollBehavior() {
        return { top: 0 };
    }
});

// Navigation guard for auth
router.beforeEach(async (to, from, next) => {
    // Check auth on first navigation
    if (authState.user === null && !authState._checked) {
        authState._checked = true;
        await authState.check();
    }

    if (to.meta.requiresAuth && !authState.authenticated) {
        next({ name: 'login', query: { next: to.fullPath } });
    } else if (to.meta.requiresAdmin && (!authState.authenticated || !authState.user?.is_admin)) {
        next({ name: 'films' });
    } else if (to.meta.guest && authState.authenticated) {
        next({ name: 'films' });
    } else {
        next();
    }
});

// Dynamic page titles
router.afterEach((to) => {
    const titles = {
        'landing': 'CinemaBook - Головна',
        'films': 'CinemaBook - Афіша',
        'film-detail': 'CinemaBook - Фільм',
        'profile': 'CinemaBook - Профіль',
        'favorites': 'CinemaBook - Обрані',
        'seats': 'CinemaBook - Вибір місць',
        'login': 'CinemaBook - Вхід',
        'register': 'CinemaBook - Реєстрація',
        'admin-dashboard': 'CinemaBook - Адмін',
        'admin-films': 'CinemaBook - Керування фільмами',
        'admin-sessions': 'CinemaBook - Керування сеансами',
        'admin-calendar': 'CinemaBook - Календар сеансів',
        'not-found': 'CinemaBook - Сторінку не знайдено'
    };
    document.title = titles[to.name] || 'CinemaBook';
});


// =====================
// === Create App ===
// =====================
const app = createApp({});
app.component('Breadcrumbs', Breadcrumbs);
app.component('BackToTop', BackToTop);
app.use(router);
app.mount('#spa-app');


// ==========================================
// === Intercept navbar links for SPA nav ===
// ==========================================
document.addEventListener('click', function(e) {
    // Handle SPA logout button
    const logoutBtn = e.target.closest('#spa-logout-btn');
    if (logoutBtn) {
        e.preventDefault();
        fetch('/api/auth/logout', { method: 'POST' })
            .then(() => {
                authState.clear();
                router.push('/login');
                showAlert('Вихід виконано', 'success');
            })
            .catch(() => showAlert('Помилка виходу', 'danger'));
        return;
    }

    const link = e.target.closest('a[href^="/app/"]');
    if (!link) return;
    const href = link.getAttribute('href');
    if (href) {
        e.preventDefault();
        router.push(href.replace('/app', '') || '/');
    }
});

// Initial auth check on load
authState.check();
