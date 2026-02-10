/* ============================================
   SCRIPT PARA INTERACTIVIDAD DE LA PÁGINA
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Seleccionar elementos del menú
    const menuToggle = document.querySelector('.header__menu-toggle');
    const nav = document.querySelector('.header__nav');
    const menuLinks = document.querySelectorAll('.header__menu a');

    // Función para abrir/cerrar el menú
    function toggleMenu() {
        menuToggle.classList.toggle('active');
        nav.classList.toggle('active');
    }

    // Evento click en el botón hamburguesa
    menuToggle.addEventListener('click', toggleMenu);

    // Cerrar menú cuando se hace click en un enlace
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            menuToggle.classList.remove('active');
            nav.classList.remove('active');
        });
    });

    // Cerrar menú cuando se hace click fuera del menú
    document.addEventListener('click', function(event) {
        const isClickInsideMenu = nav.contains(event.target);
        const isClickOnToggle = menuToggle.contains(event.target);

        if (!isClickInsideMenu && !isClickOnToggle && nav.classList.contains('active')) {
            menuToggle.classList.remove('active');
            nav.classList.remove('active');
        }
    });

    // Agregar efecto suave al desplazarse
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Aplicar observador a tarjetas de servicios
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });

    // Cambiar fondo del header al hacer scroll
    const header = document.querySelector('.header');
    let lastScrollTop = 0;

    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 50) {
            header.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
        }

        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });

    // Smooth scroll para navegadores que no lo soportan nativamente
    if (!('scrollBehavior' in document.documentElement.style)) {
        const smoothScroll = (targetId) => {
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        };

        menuLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href.startsWith('#')) {
                    e.preventDefault();
                    smoothScroll(href);
                }
            });
        });
    }
});

/* Agregar efecto de parallax suave en el hero */
window.addEventListener('scroll', function() {
    const heroImage = document.querySelector('.hero__image');
    if (heroImage) {
        const scrollY = window.pageYOffset;
        const heroTop = document.querySelector('.hero').offsetTop;
        const distance = scrollY - heroTop;

        if (distance > -window.innerHeight && distance < window.innerHeight) {
            heroImage.style.transform = `translateY(${distance * 0.5}px)`;
        }
    }
});
