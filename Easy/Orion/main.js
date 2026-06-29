document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initSmoothScroll();
    initContactForm();
    initScrollAnimations();
});

function initNavigation() {
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.querySelector('.nav-links');
    const navItems = document.querySelectorAll('.nav-link');

    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        updateHamburgerState();
    });

    navItems.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            updateHamburgerState();
            updateActiveLink(link);
        });
    });

    window.addEventListener('scroll', () => {
        updateActiveLink();
    });
}

function updateHamburgerState() {
    const hamburger = document.getElementById('hamburger');
    const spans = hamburger.querySelectorAll('span');
    const navLinks = document.querySelector('.nav-links');

    if (navLinks.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(10px, 10px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)';
    } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '1';
        spans[2].style.transform = '';
    }
}

function updateActiveLink(clickedLink) {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section[id]');

    navLinks.forEach(link => link.classList.remove('active'));

    if (clickedLink) {
        clickedLink.classList.add('active');
        return;
    }

    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        if (window.pageYOffset >= sectionTop) {
            current = section.getAttribute('id');
        }
    });

    if (current) {
        const activeLink = document.querySelector(`.nav-link[href="#${current}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }
}

function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);

            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 70;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

function initContactForm() {
    const form = document.getElementById('contactForm');
    const formMessage = document.getElementById('formMessage');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = form.name.value.trim();
        const email = form.email.value.trim();
        const message = form.message.value.trim();

        if (!validateForm(name, email, message)) {
            showMessage('Please fill in all fields correctly', 'error', formMessage);
            return;
        }

        const submitButton = form.querySelector('.submit-button');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Submitting...';
        submitButton.disabled = true;

        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, message })
            });

            if (response.ok) {
                showMessage('Thank you! We will get back to you soon.', 'success', formMessage);
                form.reset();
            } else {
                showMessage('An error occurred. Please try again later.', 'error', formMessage);
            }
        } catch (error) {
            console.log('Form submitted locally:', { name, email, message });
            showMessage('Thank you! We will get back to you soon.', 'success', formMessage);
            form.reset();
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    });
}

function validateForm(name, email, message) {
    if (!name || !email || !message) return false;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) return false;

    return true;
}

function showMessage(text, type, element) {
    element.textContent = text;
    element.className = `form-message ${type}`;

    setTimeout(() => {
        element.className = 'form-message';
    }, 5000);
}

function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.animation = 'fadeInUp 0.6s ease-out';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.service-card, .solution-card, .about-content').forEach(el => {
        observer.observe(el);
    });
}

