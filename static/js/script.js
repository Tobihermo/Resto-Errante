document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="loading"></span> Procesando...';
            }
        });
    });

    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500);
        });
    }

    const isFreeCheckbox = document.querySelector('#is_free');
    const priceField = document.querySelector('#price-field');
    
    if (isFreeCheckbox && priceField) {
        function togglePriceField() {
            if (isFreeCheckbox.checked) {
                priceField.style.display = 'none';
                priceField.querySelector('input').value = '0';
            } else {
                priceField.style.display = 'block';
            }
        }
        
        isFreeCheckbox.addEventListener('change', togglePriceField);
        togglePriceField(); 
    }
});

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(amount);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function toggleFavorite(reservationId, element) {
    fetch(`/reservation/${reservationId}/favorite`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'added') {
            showToast('Agregado a favoritos', 'success');
            if (element) {
                element.classList.add('text-danger');
            }
        } else if (data.status === 'removed') {
            showToast('Eliminado de favoritos', 'info');
            if (element) {
                element.classList.remove('text-danger');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error al actualizar favoritos', 'error');
    });
}

function checkNewNotifications() {
    if (!document.hidden) {
        updateNotificationCount();
    }
}

document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        updateNotificationCount();
    }
});

function initializeRatingStars(container) {
    const stars = container.querySelectorAll('input[type="radio"]');
    stars.forEach(star => {
        star.addEventListener('change', function() {
            const labels = container.querySelectorAll('label');
            labels.forEach(label => label.classList.remove('active'));
            this.nextElementSibling.classList.add('active');
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.rating-stars').forEach(initializeRatingStars);
    
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const reservationId = this.dataset.reservationId;
            toggleFavorite(reservationId, this);
        });
    });
    
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

function showBrowserNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/favicon.ico'
        });
    }
}
