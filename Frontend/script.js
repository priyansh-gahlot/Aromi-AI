// script.js
// DOM Elements
const themeToggle = document.getElementById('themeToggle');
const loginForm = document.getElementById('loginForm');
const quickLoginBtn = document.getElementById('quickLogin');
const passwordToggle = document.getElementById('passwordToggle');
const passwordInput = document.getElementById('password');
const emailInput = document.getElementById('email');
const container = document.querySelector('.container');
const themeLabel = document.querySelector('.theme-label');

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggle(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeToggle(newTheme);
}

function updateThemeToggle(theme) {
    const sunIcon = themeToggle.querySelector('.fa-sun');
    const moonIcon = themeToggle.querySelector('.fa-moon');
    
    if (theme === 'dark') {
        sunIcon.style.opacity = '0.5';
        moonIcon.style.opacity = '1';
        themeLabel.textContent = 'Dark Mode';
    } else {
        sunIcon.style.opacity = '1';
        moonIcon.style.opacity = '0.5';
        themeLabel.textContent = 'Light Mode';
    }
}

// Password Toggle
function togglePasswordVisibility() {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    const icon = passwordToggle.querySelector('i');
    icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
}

// Form Validation
function validateForm(email, password) {
    if (!email || !password) {
        return false;
    }
    
    if (!isValidEmail(email)) {
        return false;
    }
    
    return true;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Navigation
function navigateToDashboard() {
    // Add fade-out effect
    container.classList.add('fade-out');
    
    // Navigate after a brief pause for the animation
    setTimeout(() => {
        window.location.href = 'dashboard.html';
    }, 200);
}

// Quick Login
function quickLogin() {
    const demoEmail = 'hackathon@aromi.ai';
    emailInput.value = demoEmail;
    passwordInput.value = 'agentic_ai_demo';
    
    // Navigate immediately
    navigateToDashboard();
}

// Event Listeners
themeToggle.addEventListener('click', toggleTheme);
passwordToggle.addEventListener('click', togglePasswordVisibility);
quickLoginBtn.addEventListener('click', quickLogin);

loginForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    if (validateForm(email, password)) {
        if (rememberMe) {
            localStorage.setItem('rememberedEmail', email);
        } else {
            localStorage.removeItem('rememberedEmail');
        }
        
        navigateToDashboard();
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Set initial theme
    initTheme();
    
    // Check for remembered email
    const rememberedEmail = localStorage.getItem('rememberedEmail');
    if (rememberedEmail) {
        emailInput.value = rememberedEmail;
        document.getElementById('rememberMe').checked = true;
    }
});