/**
 * FinEasy AI - Centralized Frontend API Client
 * Interfaces with FastAPI Backend at http://127.0.0.1:8000
 */

const API_BASE_URL = window.FINEASY_API_URL
  || localStorage.getItem('fineasy_api_url')
  || (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : '');

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  getToken() {
    return localStorage.getItem('fineasy_token') || '';
  }

  setToken(token) {
    if (token) {
      localStorage.setItem('fineasy_token', token);
    } else {
      localStorage.removeItem('fineasy_token');
    }
  }

  getUser() {
    const raw = localStorage.getItem('fineasy_user');
    try {
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  setUser(user) {
    if (user) {
      localStorage.setItem('fineasy_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('fineasy_user');
    }
  }

  isAuthenticated() {
    return !!this.getToken();
  }

  logout() {
    this.setToken(null);
    this.setUser(null);
    window.location.href = 'login.html';
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = options.headers || {};

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401 && !endpoint.includes('/api/auth/')) {
          this.logout();
        }
        const errorMsg = data.error?.message || data.detail?.message || data.message || `Request failed with status ${response.status}`;
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // ---------------------------------------------------------------------------
  // AUTHENTICATION
  // ---------------------------------------------------------------------------
  async login(email, password) {
    const res = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
      this.setUser({
        user_id: res.user_id,
        email: res.email,
        name: res.name,
        user_type: res.user_type,
      });
    }
    return res;
  }

  async register(email, password, name, user_type = 'individual') {
    const res = await this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, user_type }),
    });
    if (res.access_token) {
      this.setToken(res.access_token);
      this.setUser({
        user_id: res.user_id,
        email: res.email,
        name: res.name,
        user_type: res.user_type,
      });
    }
    return res;
  }

  async getMe() {
    return this.request('/api/users/me', { method: 'GET' });
  }

  // ---------------------------------------------------------------------------
  // FILINGS
  // ---------------------------------------------------------------------------
  async getFilings() {
    return this.request('/api/filings', { method: 'GET' });
  }

  async createFiling(financial_year = '2024-25', filing_type = 'ITR') {
    return this.request('/api/filings', {
      method: 'POST',
      body: JSON.stringify({ financial_year, filing_type }),
    });
  }

  async getFiling(filingId) {
    return this.request(`/api/filings/${filingId}`, { method: 'GET' });
  }

  async updateFiling(filingId, updates) {
    return this.request(`/api/filings/${filingId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteFiling(filingId) {
    return this.request(`/api/filings/${filingId}`, { method: 'DELETE' });
  }

  // ---------------------------------------------------------------------------
  // DOCUMENTS
  // ---------------------------------------------------------------------------
  async uploadDocument(filingId, file, documentType = 'form_16') {
    const formData = new FormData();
    formData.append('filing_id', filingId);
    formData.append('document_type', documentType);
    formData.append('file', file);

    return this.request('/api/documents/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getDocument(documentId) {
    return this.request(`/api/documents/${documentId}`, { method: 'GET' });
  }

  // ---------------------------------------------------------------------------
  // AI ENGINE
  // ---------------------------------------------------------------------------
  async analyseFiling(filingId) {
    return this.request(`/api/ai/analyse/${filingId}`, { method: 'POST' });
  }

  async getAiAnalysis(filingId) {
    return this.request(`/api/ai/analysis/${filingId}`, { method: 'GET' });
  }

  async explainCalculation(filingId) {
    return this.request(`/api/ai/explain/${filingId}`, { method: 'POST' });
  }

  async setGeminiKey(apiKey, model = 'gemini-2.5-flash') {
    return this.request('/api/ai/set-key', {
      method: 'POST',
      body: JSON.stringify({ api_key: apiKey, model }),
    });
  }

  // ---------------------------------------------------------------------------
  // TAX ENGINE
  // ---------------------------------------------------------------------------
  async calculateTax(filingId, overrides = {}) {
    return this.request(`/api/tax/calculate/${filingId}`, {
      method: 'POST',
      body: JSON.stringify(overrides),
    });
  }

  async getLatestTax(filingId) {
    return this.request(`/api/tax/${filingId}`, { method: 'GET' });
  }

  async validateTax(filingId) {
    return this.request(`/api/tax/validate/${filingId}`, { method: 'POST' });
  }

  // ---------------------------------------------------------------------------
  // CA REVIEW
  // ---------------------------------------------------------------------------
  async getPendingReviews() {
    return this.request('/api/reviews/pending', { method: 'GET' });
  }

  async approveFiling(filingId, comments = 'Approved by CA') {
    return this.request(`/api/reviews/${filingId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    });
  }

  async rejectFiling(filingId, comments = 'Rejected by CA') {
    return this.request(`/api/reviews/${filingId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    });
  }

  async requestChanges(filingId, comments = 'Changes requested by CA') {
    return this.request(`/api/reviews/${filingId}/request-changes`, {
      method: 'POST',
      body: JSON.stringify({ comments }),
    });
  }

  async getReviews(filingId) {
    return this.request(`/api/reviews/${filingId}`, { method: 'GET' });
  }

  // ---------------------------------------------------------------------------
  // GOVERNMENT SUBMISSION (MOCK)
  // ---------------------------------------------------------------------------
  async getGovernmentPrefill(userId) {
    return this.request(`/api/government/prefill/${userId}`, { method: 'GET' });
  }

  async validateGovernment(filingId) {
    return this.request(`/api/government/validate/${filingId}`, { method: 'POST' });
  }

  async submitToGovernment(filingId) {
    return this.request(`/api/government/submit/${filingId}`, { method: 'POST' });
  }
}

const api = new ApiClient(API_BASE_URL);
window.api = api;
