/**
 * Vue 3 SPA with Vue Router 4
 * CinemaBook Single Page Application
 */
const { createApp } = Vue;
const { createRouter, createWebHistory } = VueRouter;


function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 4000);
}

const clientCache = {
    /**
     * РћС‚СЂРёРјР°С‚Рё РґР°РЅС– Р· РєРµС€Сѓ Р°Р±Рѕ Р·Р°РІР°РЅС‚Р°Р¶РёС‚Рё Р· СЃРµСЂРІРµСЂР°
     * @param {string} cacheKey - РєР»СЋС‡ РґР»СЏ localStorage
     * @param {function} fetchFn - С„СѓРЅРєС†С–СЏ РґР»СЏ Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ РґР°РЅРёС… Р· СЃРµСЂРІРµСЂР°
     * @param {number} ttlSeconds - С‡Р°СЃ РєРµС€СѓРІР°РЅРЅСЏ РІ СЃРµРєСѓРЅРґР°С… (Р·Р° Р·Р°РјРѕРІС‡СѓРІР°РЅРЅСЏРј 30 С…РІРёР»РёРЅ)
     */
    async getOrFetch(cacheKey, fetchFn, ttlSeconds = 1800) {
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            console.log(`вњ… Cache hit: ${cacheKey}`);
            return cached;
        }
        
        console.log(`рџ“Ґ Cache miss: ${cacheKey}, fetching from server`);
        const data = await fetchFn();
        this.setCache(cacheKey, data, ttlSeconds);
        return data;
    },
    
    /**
     * РћС‚СЂРёРјР°С‚Рё РґР°РЅС– Р· localStorage
     */
    getFromCache(cacheKey) {
        try {
            const item = localStorage.getItem(cacheKey);
            if (!item) return null;
            
            const { data, expiry } = JSON.parse(item);
            
            if (Date.now() > expiry) {
                localStorage.removeItem(cacheKey);
                return null;
            }
            
            return data;
        } catch (e) {
            console.warn(`Cache read error for ${cacheKey}:`, e);
            return null;
        }
    },
    
    /**
     * Р—Р±РµСЂРµРіС‚Рё РґР°РЅС– РІ localStorage Р· TTL
     */
    setCache(cacheKey, data, ttlSeconds = 1800) {
        try {
            const expiry = Date.now() + (ttlSeconds * 1000);
            localStorage.setItem(cacheKey, JSON.stringify({ data, expiry }));
            console.log(`рџ’ѕ Cached: ${cacheKey} (TTL: ${ttlSeconds}s)`);
        } catch (e) {
            console.warn(`Cache write error for ${cacheKey}:`, e);
        }
    },
    
    /**
     * РћС‡РёСЃС‚РёС‚Рё РєРѕРЅРєСЂРµС‚РЅРёР№ РєРµС€
     */
    clearCache(cacheKey) {
        localStorage.removeItem(cacheKey);
        console.log(`рџ—‘пёЏ  Cache cleared: ${cacheKey}`);
    },
    
    /**
     * РћС‡РёСЃС‚РёС‚Рё РІСЃС– CinemaBook РєРµС€С–
     */
    clearAllCache() {
        const keys = Object.keys(localStorage).filter(k => k.startsWith('cinema_'));
        keys.forEach(k => localStorage.removeItem(k));
        console.log(`рџ—‘пёЏ  All caches cleared (${keys.length} entries)`);
    }
};

function starsDisplay(rating) {
    return 'в­ђ'.repeat(Math.round(rating));
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

function formatMoney(value) {
    const num = Number(value || 0);
    return num.toLocaleString('uk-UA', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

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
            if (count === 0) return 'РќС–С‡РѕРіРѕ РЅРµ Р·РЅР°Р№РґРµРЅРѕ';
            if (count === 1) return '1 С„С–Р»СЊРј';
            if (count < 5) return `${count} С„С–Р»СЊРјРё`;
            return `${count} С„С–Р»СЊРјС–РІ`;
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
                    clientCache.setCache('cinema_genres', data.genres, 3600);
                }
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        async loadGenres() {
            try {
                const genres = await clientCache.getOrFetch(
                    'cinema_genres',
                    () => fetch('/api/genres').then(r => {
                        if (!r.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ');
                        return r.json().then(d => d.genres);
                    }),
                    3600  // 1 РіРѕРґРёРЅР°
                );
                if (genres && genres.length > 0) {
                    this.genres = genres;
                }
            } catch (err) {
                console.error('Load genres error:', err);
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
            if (!text) return 'РћРїРёСЃ РІС–РґСЃСѓС‚РЅС–Р№.';
            return text.length > length ? text.substring(0, length) + '...' : text;
        }
    },
    mounted() {
        const params = new URLSearchParams(window.location.search);
        this.searchQuery = params.get('q') || '';
        this.selectedGenre = params.get('genre') || '';
        this.loadGenres();  // Р—Р°РІР°РЅС‚Р°Р¶РёС‚Рё Р¶Р°РЅСЂРё Р· РєРµС€Сѓ Р°Р±Рѕ СЃРµСЂРІРµСЂР°
        this.fetchFilms();
    }
};


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
                if (!response.ok) throw new Error('Р¤С–Р»СЊРј РЅРµ Р·РЅР°Р№РґРµРЅРѕ');
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
                showAlert('Р’С–РґРіСѓРє РѕРїСѓР±Р»С–РєРѕРІР°РЅРѕ!', 'success');
            } catch (err) {
                showAlert('РџРѕРјРёР»РєР° РїСЂРё РІС–РґРїСЂР°РІС†С– РІС–РґРіСѓРєСѓ', 'danger');
            } finally {
                this.submittingReview = false;
            }
        },
        async deleteReview(reviewId) {
            if (!confirm('Р’Рё РІРїРµРІРЅРµРЅС–?')) return;
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
                    showAlert('Р’С–РґРіСѓРє РІРёРґР°Р»РµРЅРѕ', 'success');
                }
            } catch (err) {
                showAlert('РџРѕРјРёР»РєР° РїСЂРё РІРёРґР°Р»РµРЅРЅС–', 'danger');
            }
        },
        canDeleteReview(review) {
            return this.currentUserId === review.user_id || this.isAdmin;
        },
        formatDate,
        formatMoney,
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
                if (!response.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ');
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
            if (!confirm('Р’Рё РІРїРµРІРЅРµРЅС–, С‰Рѕ С…РѕС‡РµС‚Рµ СЃРєР°СЃСѓРІР°С‚Рё Р±СЂРѕРЅСЋРІР°РЅРЅСЏ?')) return;
            try {
                const response = await fetch(`/api/bookings/${bookingId}/cancel`, { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    const booking = this.bookings.find(b => b.id === bookingId);
                    if (booking) booking.is_cancelled = true;
                    showAlert('Р‘СЂРѕРЅСЋРІР°РЅРЅСЏ СЃРєР°СЃРѕРІР°РЅРѕ', 'success');
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (err) {
                showAlert('РџРѕРјРёР»РєР° СЃРєР°СЃСѓРІР°РЅРЅСЏ', 'danger');
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
                this.error = null;
                const response = await fetch('/api/favorites');
                if (!response.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ');
                const data = await response.json();
                this.favorites = data.favorites;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        async removeFavorite(filmId) {
            if (!confirm('Р’РёРґР°Р»РёС‚Рё Р· РѕР±СЂР°РЅРёС…?')) return;
            try {
                const response = await fetch(`/api/favorites/${filmId}`, { method: 'DELETE' });
                const data = await response.json();
                if (data.success) {
                    this.favorites = this.favorites.filter(f => f.id != filmId);
                    showAlert('Р’РёРґР°Р»РµРЅРѕ Р· РѕР±СЂР°РЅРёС…', 'success');
                }
            } catch (err) {
                showAlert('РџРѕРјРёР»РєР° РІРёРґР°Р»РµРЅРЅСЏ', 'danger');
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

            if (!this.email.trim()) this.errors.email = 'Р’РІРµРґС–С‚СЊ email';
            if (!this.password) this.errors.password = 'Р’РІРµРґС–С‚СЊ РїР°СЂРѕР»СЊ';
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
                    this.generalError = data.error || 'РџРѕРјРёР»РєР° РІС…РѕРґСѓ';
                }
            } catch (e) {
                this.generalError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ Р· СЃРµСЂРІРµСЂРѕРј';
            } finally {
                this.submitting = false;
            }
        }
    }
};


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
                this.errors.name = "Р†Рј'СЏ РјР°С” Р±СѓС‚Рё РјС–РЅС–РјСѓРј 2 СЃРёРјРІРѕР»Рё";
            }
            if (!this.email.trim()) this.errors.email = 'Р’РІРµРґС–С‚СЊ email';
            if (!this.password || this.password.length < 6) {
                this.errors.password = 'РџР°СЂРѕР»СЊ РјР°С” Р±СѓС‚Рё РјС–РЅС–РјСѓРј 6 СЃРёРјРІРѕР»С–РІ';
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
                    this.generalError = data.error || 'РџРѕРјРёР»РєР° СЂРµС”СЃС‚СЂР°С†С–С—';
                }
            } catch (e) {
                this.generalError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ Р· СЃРµСЂРІРµСЂРѕРј';
            } finally {
                this.submitting = false;
            }
        }
    }
};


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
            const total = this.selectedSeats.length * (this.session?.price || 0);
            return Math.round(total * 100) / 100;
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

                const response = await fetch(`/api/sessions/${this.sessionId}/seats`, { cache: 'no-store' });
                if (!response.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ РґР°РЅРёС…');
                const data = await response.json();
                
                this.session = data.session;
                this.seats = data.seats;
                this.userBookings = data.user_bookings;
                this.selectedSeats = [];
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        toggleSeat(seat) {
            if (seat.status === 'booked' || seat.status === 'blocked') return;
            const index = this.selectedSeats.indexOf(seat.id);
            if (index > -1) {
                this.selectedSeats.splice(index, 1);
            } else {
                if (this.canSelectMore) {
                    this.selectedSeats.push(seat.id);
                } else {
                    showAlert('РњР°РєСЃРёРјСѓРј 5 РјС–СЃС†СЊ РЅР° РѕРґРёРЅ СЃРµР°РЅСЃ!', 'warning');
                }
            }
        },
        isSeatSelected(seat) {
            return this.selectedSeats.includes(seat.id);
        },
        getSeatClass(seat) {
            if (seat.status === 'booked') return 'booked';
            if (seat.status === 'blocked') return 'blocked';
            if (this.isSeatSelected(seat)) return 'selected';
            return 'free';
        },
        async bookSeats() {
            if (!this.hasSelection) {
                showAlert('РћР±РµСЂС–С‚СЊ С…РѕС‡Р° Р± РѕРґРЅРµ РјС–СЃС†Рµ', 'warning');
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
                if (!response.ok) throw new Error(data.error || 'РџРѕРјРёР»РєР° Р±СЂРѕРЅСЋРІР°РЅРЅСЏ');

                const bookingIds = Array.isArray(data.booking_ids) ? data.booking_ids : [];
                if (bookingIds.length === 0) {
                    showAlert('Р‘СЂРѕРЅСЋРІР°РЅРЅСЏ СЃС‚РІРѕСЂРµРЅРѕ, Р°Р»Рµ РЅРµ РІРґР°Р»РѕСЃСЏ РїС–РґРіРѕС‚СѓРІР°С‚Рё РѕРїР»Р°С‚Сѓ.', 'warning');
                    setTimeout(() => this.$router.push({ name: 'profile' }), 1500);
                    return;
                }

                const paymentResponse = await fetch('/api/payments/create-checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ booking_ids: bookingIds })
                });
                const paymentData = await paymentResponse.json();
                if (!paymentResponse.ok || !paymentData?.payment?.checkout_url) {
                    throw new Error(paymentData.error || 'РќРµ РІРґР°Р»РѕСЃСЏ СЃС‚РІРѕСЂРёС‚Рё РїР»Р°С‚С–Р¶');
                }

                showAlert('Р‘СЂРѕРЅСЋРІР°РЅРЅСЏ СЃС‚РІРѕСЂРµРЅРѕ. РџРµСЂРµС…РѕРґРёРјРѕ РґРѕ РѕРїР»Р°С‚Рё...', 'success');
                setTimeout(() => {
                    window.location.href = paymentData.payment.checkout_url;
                }, 700);
            } catch (err) {
                showAlert(err.message, 'danger');
            } finally {
                this.booking = false;
            }
        },
        formatDateTime,
        formatMoney
    },
    mounted() {
        this.sessionId = this.$route.params.sessionId;
        if (this.sessionId) {
            this.loadSeats();
        } else {
            this.error = 'Session ID РЅРµ Р·РЅР°Р№РґРµРЅРѕ';
        }
    }
};


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
                
                const data = await clientCache.getOrFetch(
                    'cinema_popular_films',
                    () => fetch('/api/films/popular').then(r => {
                        if (!r.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ');
                        return r.json();
                    }),
                    3600  // 1 РіРѕРґРёРЅР°
                );
                
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
            return 'в­ђ'.repeat(Math.round(rating));
        },
        async toggleFavorite(film) {
            if (!authState.authenticated) {
                this.$router.push({ name: 'login' });
                return;
            }
            try {
                const method = film.is_favorite ? 'DELETE' : 'POST';
                const res = await fetch(`/api/favorites/${film.id}`, { method });
                const data = await res.json();
                if (data.success) {
                    film.is_favorite = data.action === 'added';
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (e) {
                showAlert('РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ', 'danger');
            }
        }
    },
    mounted() {
        this.loadPopularFilms();
    }
};


const AdminDashboardPage = {
    template: '#admin-dashboard-template',
    data() {
        return {
            stats: null,
            occupancyData: null,
            revenueData: null,
            loading: true,
            error: null,
            selectedHallId: null,
            halls: [],
            occupancyChart: null,
            revenueChart: null
        };
    },
    methods: {
        async loadStats() {
            try {
                this.loading = true;
                
                const statsRes = await fetch('/api/admin/stats');
                if (!statsRes.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё');
                this.stats = await statsRes.json();
                
                if (this.stats.halls_stats && this.stats.halls_stats.length > 0) {
                    this.halls = this.stats.halls_stats;
                    this.selectedHallId = this.halls[0].hall_id;
                }
                
                const occupancyRes = await fetch('/api/admin/stats/occupancy');
                const revenueRes = await fetch('/api/admin/stats/revenue');
                
                if (!occupancyRes.ok) {
                    console.error('Occupancy error:', occupancyRes.status, occupancyRes.statusText);
                } else {
                    this.occupancyData = await occupancyRes.json();
                }
                
                if (!revenueRes.ok) {
                    console.error('Revenue error:', revenueRes.status, revenueRes.statusText);
                } else {
                    this.revenueData = await revenueRes.json();
                }
                
                this.$nextTick(() => {
                    this.renderCharts();
                });

                    setTimeout(() => {
                        this.renderCharts();
                    }, 100);
                
            } catch (e) {
                this.error = e.message;
                console.error('Stats error:', e);
            } finally {
                this.loading = false;
            }
        },
        
        renderCharts() {
            const occupancyCanvas = document.getElementById('occupancyChart');
            const revenueCanvas = document.getElementById('revenueChart');
            
            if (!this.occupancyData) {
                return;
            }
            
            if (!occupancyCanvas) {
                return;
            }
            
            if (this.occupancyChart) {
                this.occupancyChart.destroy();
            }
            
            this.occupancyChart = new Chart(occupancyCanvas, {
                type: 'bar',
                data: {
                    labels: this.occupancyData.labels || [],
                    datasets: [{
                        label: 'РћРєСѓРїРѕРІР°РЅС–СЃС‚СЊ (%)',
                        data: this.occupancyData.occupancy || [],
                        backgroundColor: 'rgba(139, 92, 246, 0.8)',
                        borderColor: 'rgba(139, 92, 246, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => `${context.parsed.x.toFixed(1)}%`
                            }
                        }
                    },
                    scales: {
                        x: { max: 100 }
                    }
                }
            });
            
            if (this.revenueData && revenueCanvas) {
                if (this.revenueChart) {
                    this.revenueChart.destroy();
                }
                
                this.revenueChart = new Chart(revenueCanvas, {
                    type: 'bar',
                    data: {
                        labels: this.revenueData.labels || [],
                        datasets: [{
                            label: 'Р’РёСЂСѓС‡РєР° (UAH)',
                            data: this.revenueData.revenue || [],
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderColor: 'rgba(16, 185, 129, 1)',
                            borderWidth: 1,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        indexAxis: 'y',
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (context) => `${context.parsed.x.toFixed(2)} UAH`
                                }
                            }
                        }
                    }
                });
            }
        },
        
        switchHall(hallId) {
            this.selectedHallId = hallId;
        }
    },
    mounted() {
        this.loadStats();
    },
    beforeUnmount() {
        if (this.occupancyChart) this.occupancyChart.destroy();
        if (this.revenueChart) this.revenueChart.destroy();
    }
};


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
                if (!res.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ');
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
            if (!this.form.title.trim()) { this.formError = 'РќР°Р·РІР° РѕР±РѕРІ\'СЏР·РєРѕРІР°'; return; }
            if (!this.form.description.trim() || this.form.description.trim().length < 10) {
                this.formError = 'РћРїРёСЃ РјС–РЅС–РјСѓРј 10 СЃРёРјРІРѕР»С–РІ'; return;
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
                if (!res.ok) { this.formError = data.error || 'РџРѕРјРёР»РєР°'; return; }

                showAlert(data.message, 'success');
                this.showForm = false;
                this.editingFilm = null;
                clientCache.clearCache('cinema_popular_films');
                clientCache.clearCache('cinema_genres');
                await this.loadFilms();
            } catch (e) {
                this.formError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ';
            } finally {
                this.submitting = false;
            }
        },
        async deleteFilm(film) {
            if (!confirm(`Р’РёРґР°Р»РёС‚Рё С„С–Р»СЊРј В«${film.title}В»?`)) return;
            try {
                const res = await fetch(`/api/admin/films/${film.id}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    showAlert(data.message, 'success');
                    this.films = this.films.filter(f => f.id !== film.id);
                    clientCache.clearCache('cinema_popular_films');
                    clientCache.clearCache('cinema_genres');
                } else {
                    showAlert(data.error, 'danger');
                }
            } catch (e) {
                showAlert('РџРѕРјРёР»РєР° РІРёРґР°Р»РµРЅРЅСЏ', 'danger');
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


const AdminSessionsPage = {
    template: '#admin-sessions-template',
    data() {
        return {
            sessions: [],
            films: [],
            halls: [],
            loading: true,
            error: null,
            showForm: false,
            form: { film_id: '', hall_id: '', start_time: '', price: '' },
            submitting: false,
            formError: '',
            hallForm: { name: '', rows: 10, seats_per_row: 12 },
            editingHallId: null,
            hallSubmitting: false,
            hallError: '',
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
                this.error = null;

                const [sessionsResult, filmsResult, hallsResult] = await Promise.allSettled([
                    fetch('/api/admin/sessions'),
                    fetch('/api/admin/films'),
                    fetch('/api/admin/halls')
                ]);

                if (sessionsResult.status === 'fulfilled' && sessionsResult.value.ok) {
                    const sessData = await sessionsResult.value.json();
                    this.sessions = sessData.sessions || [];
                } else {
                    this.sessions = [];
                }

                if (filmsResult.status === 'fulfilled' && filmsResult.value.ok) {
                    const filmsData = await filmsResult.value.json();
                    this.films = filmsData.films || [];
                } else {
                    this.films = [];
                }

                if (hallsResult.status === 'fulfilled' && hallsResult.value.ok) {
                    const hallsData = await hallsResult.value.json();
                    this.halls = hallsData.halls || [];
                } else {
                    this.halls = [];
                }

                if (sessionsResult.status !== 'fulfilled' || !sessionsResult.value.ok || filmsResult.status !== 'fulfilled' || !filmsResult.value.ok || hallsResult.status !== 'fulfilled' || !hallsResult.value.ok) {
                    this.error = 'РќРµ РІРґР°Р»РѕСЃСЏ РїРѕРІРЅС–СЃС‚СЋ Р·Р°РІР°РЅС‚Р°Р¶РёС‚Рё РґР°РЅС–. Р§Р°СЃС‚РёРЅР° С„РѕСЂРјРё РјРѕР¶Рµ Р±СѓС‚Рё РЅРµРґРѕСЃС‚СѓРїРЅРѕСЋ.';
                }
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        openForm() {
            this.form = {
                film_id: '',
                hall_id: this.halls.length ? this.halls[0].id : '',
                start_time: '',
                price: ''
            };
            this.formError = '';
            this.showForm = true;
        },
        async createHall() {
            this.hallError = '';
            if (!this.hallForm.rows || !this.hallForm.seats_per_row) {
                this.hallError = 'Р—Р°РїРѕРІРЅС–С‚СЊ РїР°СЂР°РјРµС‚СЂРё Р·Р°Р»Сѓ';
                return;
            }

            this.hallSubmitting = true;
            try {
                const isEditing = this.editingHallId !== null;
                const url = isEditing ? `/api/admin/halls/${this.editingHallId}` : '/api/admin/halls';
                const method = isEditing ? 'PUT' : 'POST';
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.hallForm.name,
                        rows: parseInt(this.hallForm.rows),
                        seats_per_row: parseInt(this.hallForm.seats_per_row)
                    })
                });
                const data = await res.json();
                if (!res.ok) {
                    this.hallError = data.error || (isEditing ? 'РџРѕРјРёР»РєР° РѕРЅРѕРІР»РµРЅРЅСЏ Р·Р°Р»Сѓ' : 'РџРѕРјРёР»РєР° СЃС‚РІРѕСЂРµРЅРЅСЏ Р·Р°Р»Сѓ');
                    return;
                }
                showAlert(data.message, 'success');
                if (isEditing) {
                    const index = this.halls.findIndex(h => h.id === this.editingHallId);
                    if (index > -1) {
                        this.halls.splice(index, 1, data.hall);
                    }
                    if (this.form.hall_id === data.hall.id) {
                        this.form.hall_id = data.hall.id;
                    }
                } else {
                    this.halls.unshift(data.hall);
                    if (!this.form.hall_id) {
                        this.form.hall_id = data.hall.id;
                    }
                }
                this.hallForm = { name: '', rows: 10, seats_per_row: 12 };
                this.editingHallId = null;
            } catch (e) {
                this.hallError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ';
            } finally {
                this.hallSubmitting = false;
            }
        },
        editHall(hall) {
            this.editingHallId = hall.id;
            this.hallForm = {
                name: hall.name || '',
                rows: hall.rows || 10,
                seats_per_row: hall.seats_per_row || 12
            };
            this.hallError = '';
        },
        cancelHallEdit() {
            this.editingHallId = null;
            this.hallForm = { name: '', rows: 10, seats_per_row: 12 };
            this.hallError = '';
        },
        async deleteHall(hall) {
            if (!confirm(`Р’РёРґР°Р»РёС‚Рё Р·Р°Р» "${hall.name}"? Р¦Рµ РЅРµР·РІРѕСЂРѕС‚РЅРѕ.`)) return;
            try {
                const res = await fetch(`/api/admin/halls/${hall.id}`, { method: 'DELETE' });
                const data = await res.json();
                if (!res.ok) {
                    showAlert(data.error || 'РџРѕРјРёР»РєР° РІРёРґР°Р»РµРЅРЅСЏ Р·Р°Р»Сѓ', 'danger');
                    return;
                }
                showAlert(data.message || 'Р—Р°Р» РІРёРґР°Р»РµРЅРѕ', 'success');
                this.halls = this.halls.filter(h => h.id !== hall.id);
                if (this.form.hall_id === hall.id) this.form.hall_id = this.halls.length ? this.halls[0].id : '';
                if (this.editingHallId === hall.id) {
                    this.cancelHallEdit();
                }
            } catch (e) {
                showAlert('РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ РїСЂРё РІРёРґР°Р»РµРЅРЅС– Р·Р°Р»Сѓ', 'danger');
            }
        },
        async submitForm() {
            this.formError = '';
            if (!this.form.film_id || !this.form.hall_id || !this.form.start_time || !this.form.price) {
                this.formError = 'Р—Р°РїРѕРІРЅС–С‚СЊ РІСЃС– РїРѕР»СЏ'; return;
            }
            this.submitting = true;
            try {
                const payload = {
                    film_id: parseInt(this.form.film_id),
                    hall_id: parseInt(this.form.hall_id),
                    start_time: this.form.start_time.replace('T', ' '),
                    price: parseFloat(this.form.price)
                };
                const res = await fetch('/api/admin/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) { this.formError = data.error || 'РџРѕРјРёР»РєР°'; return; }
                showAlert(data.message, 'success');
                if (data.session) {
                    this.sessions.unshift(data.session);
                }
                this.showForm = false;
                await this.loadData();
            } catch (e) {
                this.formError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ';
            } finally {
                this.submitting = false;
            }
        },
        async cancelSession(session) {
            if (!confirm(`РЎРєР°СЃСѓРІР°С‚Рё СЃРµР°РЅСЃ "${session.film_title}" (${session.start_time})?`)) return;
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
                showAlert('РџРѕРјРёР»РєР° СЃРєР°СЃСѓРІР°РЅРЅСЏ', 'danger');
            }
        },
        formatDateTime
    },
    mounted() {
        this.loadData();
    }
};


const AdminHallEditorPage = {
    template: '#admin-hall-editor-template',
    data() {
        return {
            sessionId: null,
            session: null,
            seats: [],
            layout: { rows: 10, seats_per_row: 12 },
            loading: true,
            saving: false,
            error: null,
            formError: ''
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
        bookedSeatsCount() {
            return this.seats.filter(seat => seat.status === 'booked').length;
        },
        blockedSeatsCount() {
            return this.seats.filter(seat => seat.status === 'blocked').length;
        },
        freeSeatsCount() {
            return this.seats.filter(seat => seat.status === 'free').length;
        },
        canResize() {
            return !this.session || this.session.can_resize;
        }
    },
    methods: {
        async loadHall() {
            try {
                this.loading = true;
                this.error = null;
                const response = await fetch(`/api/admin/sessions/${this.sessionId}/hall`, { cache: 'no-store' });
                if (!response.ok) throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ СЃС…РµРјРё Р·Р°Р»Сѓ');
                const data = await response.json();
                this.session = data.session;
                this.layout = data.layout;
                this.seats = data.seats;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },
        toggleSeat(seat) {
            if (seat.status === 'booked') return;
            seat.status = seat.status === 'blocked' ? 'free' : 'blocked';
        },
        setAllSeats(status) {
            this.seats.forEach(seat => {
                if (seat.status !== 'booked') {
                    seat.status = status === 'blocked' ? 'blocked' : 'free';
                }
            });
        },
        async saveHall() {
            this.formError = '';
            this.saving = true;
            try {
                const payload = {
                    rows: this.layout.rows,
                    seats_per_row: this.layout.seats_per_row,
                    seats: this.seats.map(seat => ({
                        row: seat.row,
                        number: seat.number,
                        status: seat.status
                    }))
                };
                const response = await fetch(`/api/admin/sessions/${this.sessionId}/hall`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                if (!response.ok) {
                    this.formError = data.error || 'РџРѕРјРёР»РєР° Р·Р±РµСЂРµР¶РµРЅРЅСЏ СЃС…РµРјРё Р·Р°Р»Сѓ';
                    return;
                }
                showAlert(data.message, 'success');
                await this.loadHall();
            } catch (err) {
                this.formError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ Р· СЃРµСЂРІРµСЂРѕРј';
            } finally {
                this.saving = false;
            }
        },
        formatDateTime,
        formatMoney
    },
    mounted() {
        this.sessionId = this.$route.params.sessionId;
        this.loadHall();
    }
};


const AdminCalendarPage = {
    template: '#admin-calendar-template',
    data() {
        return {
            weekDays: [],
            timeSlots: [],
            sessionsGrid: {},
            films: [],
            halls: [],
            selectedHallId: '',
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
                hall_id: '',
                price: 150
            },
            submitting: false
        };
    },
    computed: {
        currentHall() {
            return this.halls.find(hall => hall.id === this.selectedHallId) || null;
        }
    },
    methods: {
        syncCalendarUrl() {
            const params = new URLSearchParams();
            if (this.weekOffset) params.set('week', this.weekOffset);
            if (this.selectedHallId) params.set('hall_id', this.selectedHallId);
            const query = params.toString();
            const nextUrl = query ? `/app/admin/calendar?${query}` : '/app/admin/calendar';
            window.history.replaceState({}, '', nextUrl);
        },
        async loadCalendar() {
            try {
                this.loading = true;
                this.error = null;
                const [calendarResult, hallsResult] = await Promise.allSettled([
                    fetch(`/api/admin/calendar?week=${this.weekOffset}${this.selectedHallId ? `&hall_id=${this.selectedHallId}` : ''}`),
                    fetch('/api/admin/halls')
                ]);

                if (calendarResult.status === 'fulfilled' && calendarResult.value.ok) {
                    const data = await calendarResult.value.json();
                    this.weekDays = data.week_days;
                    this.timeSlots = data.time_slots;
                    this.sessionsGrid = data.sessions_grid;
                    this.films = data.films;
                    this.halls = data.halls || [];
                    this.selectedHallId = data.selected_hall_id || this.selectedHallId || (this.halls[0] && this.halls[0].id) || '';
                    this.startOfWeek = data.start_of_week;
                } else {
                    throw new Error('РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ');
                }

                if (hallsResult.status === 'fulfilled' && hallsResult.value.ok) {
                    const hallsData = await hallsResult.value.json();
                    if (!this.halls.length) {
                        this.halls = hallsData.halls || [];
                    }
                    if (!this.selectedHallId && this.halls.length) {
                        this.selectedHallId = this.halls[0].id;
                    }
                } else {
                    if (!this.halls.length) this.halls = [];
                }
                this.syncCalendarUrl();
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        switchHall(hallId) {
            this.selectedHallId = hallId;
            this.syncCalendarUrl();
            this.loadCalendar();
        },
        prevWeek() {
            this.weekOffset--;
            this.syncCalendarUrl();
            this.loadCalendar();
        },
        nextWeek() {
            this.weekOffset++;
            this.syncCalendarUrl();
            this.loadCalendar();
        },
        currentWeek() {
            this.weekOffset = 0;
            this.syncCalendarUrl();
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
            this.createForm.hall_id = this.selectedHallId || (this.halls.length ? this.halls[0].id : '');
            this.createForm.price = 150;
            this.showModal = true;
        },
        async createSession() {
            if (!this.createForm.film_id || !this.createForm.hall_id || !this.createForm.price) {
                showAlert('Р—Р°РїРѕРІРЅС–С‚СЊ РІСЃС– РїРѕР»СЏ', 'danger');
                return;
            }
            this.submitting = true;
            try {
                const res = await fetch('/api/admin/calendar/create-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        film_id: parseInt(this.createForm.film_id),
                        hall_id: parseInt(this.createForm.hall_id),
                        date: this.modalData.date,
                        time: this.modalData.time,
                        price: parseFloat(this.createForm.price)
                    })
                });
                const data = await res.json();
                if (!res.ok) {
                    showAlert(data.error || 'РџРѕРјРёР»РєР° СЃС‚РІРѕСЂРµРЅРЅСЏ', 'danger');
                    return;
                }
                showAlert(data.message, 'success');
                this.showModal = false;
                await this.loadCalendar();
            } catch (e) {
                showAlert('РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ', 'danger');
            } finally {
                this.submitting = false;
            }
        },
        async cancelSession(sessionId, event) {
            if (event) event.stopPropagation();
            if (!confirm('Р’Рё РІРїРµРІРЅРµРЅС–, С‰Рѕ С…РѕС‡РµС‚Рµ СЃРєР°СЃСѓРІР°С‚Рё С†РµР№ СЃРµР°РЅСЃ?')) return;
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
                showAlert('РџРѕРјРёР»РєР° СЃРєР°СЃСѓРІР°РЅРЅСЏ', 'danger');
            }
        },
        weekLabel() {
            if (this.weekOffset === 0) return 'рџ“… РџРѕС‚РѕС‡РЅРёР№ С‚РёР¶РґРµРЅСЊ';
            if (this.weekOffset === 1) return 'рџ“… РќР°СЃС‚СѓРїРЅРёР№ С‚РёР¶РґРµРЅСЊ';
            if (this.weekOffset > 1) return `рџ“… +${this.weekOffset} С‚РёР¶РЅС–РІ`;
            return `рџ“… ${this.weekOffset} С‚РёР¶РЅС–РІ РЅР°Р·Р°Рґ`;
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
        const params = new URLSearchParams(window.location.search);
        const hallParam = params.get('hall_id');
        if (hallParam) {
            this.selectedHallId = parseInt(hallParam);
        }
        const weekParam = params.get('week');
        if (weekParam) {
            this.weekOffset = parseInt(weekParam);
        }
        this.loadCalendar();
    }
};


const AdminScannerPage = {
    template: '#admin-scanner-template',
    data() {
        return {
            tokenInput: '',
            scanning: false,
            scanResult: null,
            scanError: null
        };
    },
    methods: {
        normalizeToken(raw) {
            const value = (raw || '').trim();
            if (!value) return '';
            if (value.startsWith('cinemabook:ticket:')) {
                return value.split('cinemabook:ticket:', 1)[0] ? value : value.replace('cinemabook:ticket:', '');
            }
            return value;
        },
        async scanTicket() {
            this.scanError = null;
            this.scanResult = null;

            const token = this.tokenInput.trim().startsWith('cinemabook:ticket:')
                ? this.tokenInput.trim().replace('cinemabook:ticket:', '')
                : this.tokenInput.trim();

            if (!token) {
                this.scanError = 'Р’СЃС‚Р°РІС‚Рµ QR-С‚РѕРєРµРЅ Р°Р±Рѕ РїРѕРІРЅРёР№ QR payload';
                return;
            }

            this.scanning = true;
            try {
                const res = await fetch('/api/admin/tickets/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token })
                });
                const data = await res.json();

                if (!res.ok) {
                    this.scanError = data.error || 'РџРѕРјРёР»РєР° РїРµСЂРµРІС–СЂРєРё РєРІРёС‚РєР°';
                    this.scanResult = data.ticket || null;
                    return;
                }

                this.scanResult = data.ticket || null;
                showAlert(data.message || 'РљРІРёС‚РѕРє РІР°Р»С–РґРЅРёР№', 'success');
                this.tokenInput = '';
            } catch (e) {
                this.scanError = 'РџРѕРјРёР»РєР° Р·\'С”РґРЅР°РЅРЅСЏ Р· СЃРµСЂРІРµСЂРѕРј';
            } finally {
                this.scanning = false;
            }
        }
    }
};


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
            const items = [{ label: 'Р“РѕР»РѕРІРЅР°', path: '/', icon: 'fas fa-home' }];
            
            if (route.name === 'landing') return [];
            if (route.name === 'films') {
                items.push({ label: 'Р¤С–Р»СЊРјРё', path: '/films', icon: 'fas fa-film' });
            } else if (route.name === 'film-detail') {
                items.push({ label: 'Р¤С–Р»СЊРјРё', path: '/films', icon: 'fas fa-film' });
                items.push({ label: 'Р”РµС‚Р°Р»С– С„С–Р»СЊРјСѓ', path: route.path });
            } else if (route.name === 'favorites') {
                items.push({ label: 'РћР±СЂР°РЅС–', path: '/favorites', icon: 'fas fa-heart' });
            } else if (route.name === 'profile') {
                items.push({ label: 'РџСЂРѕС„С–Р»СЊ', path: '/profile', icon: 'fas fa-user' });
            } else if (route.name === 'seats') {
                items.push({ label: 'Р¤С–Р»СЊРјРё', path: '/films', icon: 'fas fa-film' });
                items.push({ label: 'Р’РёР±С–СЂ РјС–СЃС†СЊ', path: route.path, icon: 'fas fa-couch' });
            } else if (route.name === 'login') {
                items.push({ label: 'Р’С…С–Рґ', path: '/login', icon: 'fas fa-sign-in-alt' });
            } else if (route.name === 'register') {
                items.push({ label: 'Р РµС”СЃС‚СЂР°С†С–СЏ', path: '/register', icon: 'fas fa-user-plus' });
            } else if (route.name && route.name.startsWith('admin')) {
                items.push({ label: 'РђРґРјС–РЅ-РїР°РЅРµР»СЊ', path: '/admin', icon: 'fas fa-cog' });
                if (route.name === 'admin-films') {
                    items.push({ label: 'Р¤С–Р»СЊРјРё', path: '/admin/films', icon: 'fas fa-film' });
                } else if (route.name === 'admin-sessions') {
                    items.push({ label: 'РЎРµР°РЅСЃРё', path: '/admin/sessions', icon: 'fas fa-ticket-alt' });
                } else if (route.name === 'admin-hall-editor') {
                    items.push({ label: 'РЎРµР°РЅСЃРё', path: '/admin/sessions', icon: 'fas fa-ticket-alt' });
                    items.push({ label: 'Р РµРґР°РєС‚РѕСЂ Р·Р°Р»Сѓ', path: route.path, icon: 'fas fa-couch' });
                } else if (route.name === 'admin-calendar') {
                    items.push({ label: 'РљР°Р»РµРЅРґР°СЂ', path: '/admin/calendar', icon: 'fas fa-calendar-week' });
                } else if (route.name === 'admin-scanner') {
                    items.push({ label: 'РЎРєР°РЅРµСЂ РєРІРёС‚РєС–РІ', path: '/admin/scanner', icon: 'fas fa-qrcode' });
                }
            }
            
            return items;
        }
    }
};


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
    { path: '/admin/sessions/:sessionId/hall', name: 'admin-hall-editor', component: AdminHallEditorPage, meta: { requiresAdmin: true } },
    { path: '/admin/calendar', name: 'admin-calendar', component: AdminCalendarPage, meta: { requiresAdmin: true } },
    { path: '/admin/scanner', name: 'admin-scanner', component: AdminScannerPage, meta: { requiresAdmin: true } },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundPage }
];

const router = createRouter({
    history: createWebHistory('/app'),
    routes,
    scrollBehavior() {
        return { top: 0 };
    }
});

router.beforeEach(async (to, from, next) => {
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

router.afterEach((to) => {
    const titles = {
        'landing': 'CinemaBook - Р“РѕР»РѕРІРЅР°',
        'films': 'CinemaBook - РђС„С–С€Р°',
        'film-detail': 'CinemaBook - Р¤С–Р»СЊРј',
        'profile': 'CinemaBook - РџСЂРѕС„С–Р»СЊ',
        'favorites': 'CinemaBook - РћР±СЂР°РЅС–',
        'seats': 'CinemaBook - Р’РёР±С–СЂ РјС–СЃС†СЊ',
        'login': 'CinemaBook - Р’С…С–Рґ',
        'register': 'CinemaBook - Р РµС”СЃС‚СЂР°С†С–СЏ',
        'admin-dashboard': 'CinemaBook - РђРґРјС–РЅ',
        'admin-films': 'CinemaBook - РљРµСЂСѓРІР°РЅРЅСЏ С„С–Р»СЊРјР°РјРё',
        'admin-sessions': 'CinemaBook - РљРµСЂСѓРІР°РЅРЅСЏ СЃРµР°РЅСЃР°РјРё',
        'admin-hall-editor': 'CinemaBook - Р РµРґР°РєС‚РѕСЂ Р·Р°Р»Сѓ',
        'admin-calendar': 'CinemaBook - РљР°Р»РµРЅРґР°СЂ СЃРµР°РЅСЃС–РІ',
        'admin-scanner': 'CinemaBook - РЎРєР°РЅРµСЂ РєРІРёС‚РєС–РІ',
        'not-found': 'CinemaBook - РЎС‚РѕСЂС–РЅРєСѓ РЅРµ Р·РЅР°Р№РґРµРЅРѕ'
    };
    document.title = titles[to.name] || 'CinemaBook';
});


const app = createApp({});
app.component('Breadcrumbs', Breadcrumbs);
app.component('BackToTop', BackToTop);
app.use(router);
app.mount('#spa-app');


document.addEventListener('click', function(e) {
    const logoutBtn = e.target.closest('#spa-logout-btn');
    if (logoutBtn) {
        e.preventDefault();
        fetch('/api/auth/logout', { method: 'POST' })
            .then(() => {
                authState.clear();
                router.push('/login');
                showAlert('Р’РёС…С–Рґ РІРёРєРѕРЅР°РЅРѕ', 'success');
            })
            .catch(() => showAlert('РџРѕРјРёР»РєР° РІРёС…РѕРґСѓ', 'danger'));
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

authState.check();
