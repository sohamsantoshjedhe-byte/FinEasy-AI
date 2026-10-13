/**
 * FinEasy AI - Common Frontend Application Logic & UI Helpers
 */

function formatINR(val) {
  if (val === undefined || val === null || isNaN(val)) return '₹0.00';
  const num = Number(val);
  return '₹' + num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bgColors = {
    success: 'bg-[#182a20] border-[#3ddc97] text-[#3ddc97]',
    error: 'bg-[#2d1818] border-[#ff7c7c] text-[#ff7c7c]',
    info: 'bg-[#181e2d] border-[#7c9cff] text-[#7c9cff]',
  };

  const icons = {
    success: 'check_circle',
    error: 'error',
    info: 'info',
  };

  toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-md shadow-2xl transition-all duration-300 transform translate-y-4 opacity-0 pointer-events-auto ${bgColors[type] || bgColors.info}`;
  toast.innerHTML = `
    <span class="material-symbols-outlined text-[20px]">${icons[type] || 'info'}</span>
    <span class="font-label-md text-label-md text-on-surface font-medium">${message}</span>
  `;

  toastContainer.appendChild(toast);

  // Trigger entrance
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  });

  // Auto remove
  setTimeout(() => {
    toast.classList.add('translate-y-4', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function getActiveFilingId() {
  const params = new URLSearchParams(window.location.search);
  const idFromUrl = params.get('filing_id');
  if (idFromUrl) {
    localStorage.setItem('fineasy_active_filing', idFromUrl);
    return idFromUrl;
  }
  return localStorage.getItem('fineasy_active_filing') || '';
}

function setActiveFilingId(filingId) {
  if (filingId) {
    localStorage.setItem('fineasy_active_filing', filingId);
  }
}

// Initialize Application UI
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname.split('/').pop() || 'index.html';
  const isProtectedPage = ['dashboard.html', 'upload.html', 'tax-result.html', 'ca-review.html'].includes(path);

  // Check Authentication on protected pages
  if (isProtectedPage && !window.api.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  // Populate User info in sidebar if logged in
  const currentUser = window.api.getUser();
  if (currentUser) {
    const userNames = document.querySelectorAll('.user-display-name');
    userNames.forEach(el => el.textContent = currentUser.name || 'Taxpayer');

    const userEmails = document.querySelectorAll('.user-display-email');
    userEmails.forEach(el => el.textContent = currentUser.email || 'taxpayer@demo.in');

    const userRoles = document.querySelectorAll('.user-display-role');
    userRoles.forEach(el => el.textContent = currentUser.user_type === 'ca' ? 'CA Verified' : 'Individual');
  }

  // Set active link in sidebar navigation
  const navLinks = document.querySelectorAll('aside nav a, header nav a');
  navLinks.forEach(link => {
    const dataPath = link.getAttribute('data-path');
    const href = link.getAttribute('href');

    let isActive = false;
    if (dataPath) {
      if (path.includes(dataPath)) isActive = true;
      if (path === 'index.html' && dataPath === 'home') isActive = true;
    }

    if (isActive) {
      link.classList.add('bg-surface-container-high', 'text-on-surface', 'font-semibold');
      link.classList.remove('text-on-surface-variant');
      link.setAttribute('aria-current', 'page');
    }
  });

  // Attach logout handler
  const logoutBtns = document.querySelectorAll('[data-path="logout"]');
  logoutBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      window.api.logout();
    });
  });
});
