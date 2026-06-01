const API_BASE = 'http://127.0.0.1:8000/api';

function getToken() {
    return localStorage.getItem('access_token');
}

function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function setUserData(data) {
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify({
        id: data.user_id,
        username: data.username,
        role: data.role
    }));
}

function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });
    } catch (networkErr) {
        throw new Error('Network error: ' + networkErr.message);
    }

    if (response.status === 401) {
        clearAuth();
        window.location.href = '/';
        return null;
    }

    const contentType = response.headers.get('content-type') || '';

    if (!contentType.includes('application/json')) {
        const text = await response.text();
        if (!response.ok) {
            // Extract meaningful error from HTML if possible
            const match = text.match(/<title>(.*?)<\/title>/i);
            const htmlTitle = match ? match[1] : '';
            throw new Error(`Server error ${response.status}${htmlTitle ? ': ' + htmlTitle : ''} — endpoint may not exist: ${API_BASE}${endpoint}`);
        }
        return text;
    }

    const data = await response.json();

    if (!response.ok) {
        const msg = data && (data.detail || data.error || data.message)
            ? (data.detail || data.error || data.message)
            : JSON.stringify(data);
        throw new Error(msg);
    }

    return data;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => { toast.className = 'toast'; }, 3000);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function logout() {
    clearAuth();
    window.location.href = '/';
}

// Exposed globally so dashboard.html can call it after payment
window.refreshAllBillsTable = async function() {
    try {
        const bills = await apiRequest('/bills/');
        const tbody = document.querySelector('.billing-main .table-container:last-child tbody');
        if (!tbody) return;
        tbody.innerHTML = bills.map(b => `
            <tr>
                <td>#${b.id}</td>
                <td>${b.patient_name}</td>
                <td>$${b.total_amount}</td>
                <td>$${b.paid_amount}</td>
                <td>$${b.due_amount}</td>
                <td>${formatDate(b.bill_date)}</td>
                <td><span class="status-badge status-${b.status}">${b.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="viewBill(${b.id})">View</button>
                    ${b.status !== 'paid' ? `<button class="btn btn-sm btn-success" onclick="showAddPaymentModal(${b.id})">Pay</button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Failed to refresh bills table:', e);
    }
};