const API_URL = window.APP_CONFIG?.API_URL || 'http://127.0.0.1:8002'; // FastAPI backend address

const decodeJwtPayload = (token) => {
    const payloadPart = token.split('.')[1];
    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
    return JSON.parse(atob(padded));
};

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const toggleBtn = document.getElementById('toggle-form');
    const formTitle = document.getElementById('form-title');
    const formSubtitle = document.getElementById('form-subtitle');
    const toggleText = document.getElementById('toggle-text');

    let isLogin = true;

    toggleBtn.addEventListener('click', () => {
        isLogin = !isLogin;
        if (isLogin) {
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            formTitle.innerText = "Welcome Back";
            formSubtitle.innerText = "Please sign in to your account";
            toggleText.innerText = "Don't have an account?";
            toggleBtn.innerText = "Sign Up";
        } else {
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            formTitle.innerText = "Create Account";
            formSubtitle.innerText = "Join the Complaint Management System";
            toggleText.innerText = "Already have an account?";
            toggleBtn.innerText = "Sign In";
        }
    });

    // Handle Login
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        try {
            const response = await fetch(`${API_URL}/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);

                // Parse JWT to check role
                const payload = decodeJwtPayload(data.access_token);
                localStorage.setItem('role', payload.role);
                localStorage.setItem('email', payload.sub);

                if (payload.role === 'admin') {
                    window.location.href = 'admin.html';
                } else {
                    window.location.href = 'dashboard.html';
                }
            } else {
                const data = await response.json();
                alert(data.detail || 'Invalid email or password');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Failed to connect to server');
        }
    });

    // Handle Registration
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;

        try {
            const response = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, role: 'user' })
            });

            if (response.ok) {
                alert('Account created! Please sign in.');
                toggleBtn.click();
            } else {
                const data = await response.json();
                alert(data.detail || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('Failed to connect to server');
        }
    });
});
