document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".site-nav");
  const navLinks = document.querySelectorAll(".site-nav a");
  const form = document.getElementById("contactForm");
  const formStatus = document.getElementById("formStatus");

  if (toggle && nav) {
    const setMenuState = (isOpen) => {
      toggle.classList.toggle("is-open", isOpen);
      nav.classList.toggle("is-open", isOpen);
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.setAttribute("aria-label", isOpen ? "Cerrar menú principal" : "Abrir menú principal");
    };

    toggle.addEventListener("click", () => {
      const isOpen = !nav.classList.contains("is-open");
      setMenuState(isOpen);
    });

    navLinks.forEach((link) => {
      link.addEventListener("click", () => setMenuState(false));
    });

    document.addEventListener("click", (event) => {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) {
        setMenuState(false);
      }
    });
  }

  const revealItems = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 }
  );

  revealItems.forEach((item) => observer.observe(item));

  if (form) {
    const fields = {
      nombre: {
        element: document.getElementById("nombre"),
        error: document.getElementById("error-nombre"),
        validate: (value) => value.trim().length >= 2,
        message: "Ingresa un nombre válido.",
      },
      email: {
        element: document.getElementById("email"),
        error: document.getElementById("error-email"),
        validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        message: "Ingresa un email válido.",
      },
      tipo: {
        element: document.getElementById("tipo"),
        error: document.getElementById("error-tipo"),
        validate: (value) => value.trim() !== "",
        message: "Selecciona el tipo de negocio.",
      },
      mensaje: {
        element: document.getElementById("mensaje"),
        error: document.getElementById("error-mensaje"),
        validate: (value) => value.trim().length >= 12,
        message: "Describe tu necesidad con al menos 12 caracteres.",
      },
    };

    const showError = (field, message) => {
      field.error.textContent = message;
      field.element.setAttribute("aria-invalid", "true");
    };

    const clearError = (field) => {
      field.error.textContent = "";
      field.element.removeAttribute("aria-invalid");
    };

    const validateField = (field) => {
      if (!field.validate(field.element.value)) {
        showError(field, field.message);
        return false;
      }
      clearError(field);
      return true;
    };

    Object.values(fields).forEach((field) => {
      field.element.addEventListener("blur", () => validateField(field));
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      formStatus.textContent = "";

      let isValid = true;
      Object.values(fields).forEach((field) => {
        if (!validateField(field)) {
          isValid = false;
        }
      });

      if (!isValid) {
        formStatus.textContent = "Revisa los campos marcados para continuar.";
        return;
      }

      formStatus.textContent = "Enviando solicitud...";
      try {
        const response = await fetch("https://formsubmit.co/ajax/ventas@art4hotel.com", {
          method: "POST",
          body: new FormData(form),
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Respuesta no valida del servicio.");
        }

        formStatus.textContent = "Solicitud enviada. Revisa ventas@art4hotel.com para confirmar el primer envio.";
        form.reset();
      } catch (error) {
        formStatus.textContent = "No se pudo enviar por AJAX. Enviando por metodo normal...";
        form.submit();
      }
    });
  }
});
