// Google OAuth Authentication Guard & Dedicated Login Handler

const IS_LOGIN_PAGE = window.location.pathname.endsWith('login.html');

async function checkAuth() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      if (IS_LOGIN_PAGE) {
        // If already logged in and on login.html, redirect to main dashboard
        window.location.href = 'index.html';
      } else {
        renderUserHeader(data.email);
      }
    } else {
      if (!IS_LOGIN_PAGE) {
        // Redirect to login page if unauthenticated
        window.location.href = 'login.html';
      } else {
        initGoogleSignIn();
      }
    }
  } catch (err) {
    if (!IS_LOGIN_PAGE) {
      window.location.href = 'login.html';
    } else {
      initGoogleSignIn();
    }
  }
}

async function initGoogleSignIn() {
  try {
    const res = await fetch('/api/auth/config');
    if (!res.ok) return;
    const data = await res.json();
    const clientId = data.google_client_id;

    const errorEl = document.getElementById('auth-error');

    if (!clientId || clientId.includes("GANTI_DENGAN")) {
      if (errorEl) {
        errorEl.textContent = 'Server belum mengkonfigurasi GOOGLE_CLIENT_ID di file .env';
        errorEl.style.display = 'block';
      }
      return;
    }

    if (window.google && google.accounts && google.accounts.id) {
      google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse
      });
      google.accounts.id.renderButton(
        document.getElementById("g_id_signin"),
        { theme: "filled_blue", size: "large", type: "standard", shape: "pill", width: 280 }
      );
    } else {
      setTimeout(initGoogleSignIn, 300);
    }
  } catch (err) {
    console.error("Failed to fetch auth config", err);
  }
}

async function handleCredentialResponse(response) {
  const errorEl = document.getElementById('auth-error');
  if (errorEl) errorEl.style.display = 'none';

  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: response.credential })
    });

    if (res.ok) {
      // Redirect to dashboard on successful login
      window.location.href = 'index.html';
    } else {
      const err = await res.json();
      if (errorEl) {
        errorEl.textContent = err.detail || "Akses ditolak: Email Anda tidak terdaftar dalam whitelist.";
        errorEl.style.display = 'block';
      }
    }
  } catch (e) {
    if (errorEl) {
      errorEl.textContent = "Gagal terhubung ke server auth.";
      errorEl.style.display = 'block';
    }
  }
}

function renderUserHeader(email) {
  const navbarRight = document.querySelector('.navbar-right');
  if (!navbarRight) return;

  let userBadge = document.getElementById('user-profile-badge');
  if (!userBadge) {
    userBadge = document.createElement('div');
    userBadge.id = 'user-profile-badge';
    userBadge.style.cssText = "display: flex; align-items: center; gap: 10px; background: #FFFFFF; padding: 6px 16px; border-radius: 999px; font-size: 0.85rem; color: #020002; border: 1px solid #EAE5DD; font-weight: 600; box-shadow: 0 2px 10px rgba(0,0,0,0.03);";
    userBadge.innerHTML = `
      <span><span id="user-email-text">${email}</span></span>
      <button id="btn-logout" style="background: rgba(225, 29, 72, 0.08); border: 1px solid rgba(225, 29, 72, 0.2); color: #E11D48; cursor: pointer; font-size: 0.75rem; font-weight: 700; padding: 5px 12px; border-radius: 999px; transition: all 0.2s;">Logout</button>
    `;


    navbarRight.appendChild(userBadge);

    document.getElementById('btn-logout').addEventListener('click', async () => {
      await fetch('/api/auth/logout', { method: 'POST' });
      window.location.href = 'login.html';
    });
  } else {
    document.getElementById('user-email-text').textContent = email;
  }
}


// Auto check auth on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', checkAuth);
} else {
  checkAuth();
}
