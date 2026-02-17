document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".site-nav");
  const navLinks = document.querySelectorAll(".site-nav a");
  const catalogTabs = document.querySelectorAll(".catalog-tab");
  const catalogPanel = document.getElementById("catalogPanel");
  const catalogTitle = document.getElementById("catalogTitle");
  const catalogDesc = document.getElementById("catalogDesc");
  const catalogGrid = document.getElementById("catalogGrid");
  const catalogNote = document.getElementById("catalogNote");
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

  const catalogData = {
    bolsas: {
      title: "Catálogo de Bolsas",
      desc: "Una muestra de bolsas boutique y opciones para proyectos personalizados.",
      note: "4 espacios más: Próximamente.",
      items: [
        { type: "image", src: "Recursos/bolsa-boutique.png", alt: "Bolsa boutique (muestra de catálogo)" },
        { type: "image", src: "Recursos/bolsa-2026.png", alt: "Bolsa 2026 (muestra de catálogo)" },
        { type: "placeholder" },
        { type: "placeholder" },
        { type: "placeholder" },
        { type: "placeholder" },
      ],
    },
    amenidades: {
      title: "Catálogo de Amenidades",
      desc: "Líneas de amenidades para baño y habitación. Imágenes próximamente.",
      note: "Próximamente agregaremos fotografías del catálogo.",
      items: Array.from({ length: 6 }, () => ({ type: "placeholder" })),
    },
    blancos: {
      title: "Catálogo de Blancos",
      desc: "Ropa de cama, toallas y textiles. Imágenes próximamente.",
      note: "Próximamente agregaremos fotografías del catálogo.",
      items: Array.from({ length: 6 }, () => ({ type: "placeholder" })),
    },
    accesorios: {
      title: "Catálogo de Accesorios",
      desc: "Accesorios y complementos para operación y experiencia. Imágenes próximamente.",
      note: "Próximamente agregaremos fotografías del catálogo.",
      items: Array.from({ length: 6 }, () => ({ type: "placeholder" })),
    },
  };

  const renderCatalog = (key) => {
    if (!catalogTitle || !catalogDesc || !catalogGrid || !catalogPanel) {
      return;
    }

    const catalog = catalogData[key];
    if (!catalog) {
      return;
    }

    catalogTitle.textContent = catalog.title;
    catalogDesc.textContent = catalog.desc;
    if (catalogNote) {
      catalogNote.textContent = catalog.note || "";
    }
    catalogGrid.textContent = "";

    catalog.items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "catalog-item";

      if (item.type === "image") {
        const img = document.createElement("img");
        img.src = item.src;
        img.alt = item.alt || "";
        img.loading = "lazy";
        card.appendChild(img);
      } else {
        const ph = document.createElement("div");
        ph.className = "catalog-placeholder";
        ph.textContent = "Próximamente";
        card.appendChild(ph);
      }

      catalogGrid.appendChild(card);
    });
  };

  const setActiveCatalog = (tab) => {
    const key = tab?.dataset?.catalog;
    if (!key) return;

    catalogTabs.forEach((t) => {
      const isActive = t === tab;
      t.classList.toggle("is-active", isActive);
      t.setAttribute("aria-selected", String(isActive));
      t.tabIndex = isActive ? 0 : -1;
    });

    if (catalogPanel) {
      catalogPanel.setAttribute("aria-labelledby", tab.id);
    }

    renderCatalog(key);
  };

  if (catalogTabs.length && catalogGrid && catalogTitle && catalogDesc) {
    catalogTabs.forEach((tab) => {
      tab.addEventListener("click", () => setActiveCatalog(tab));
    });

    // Initial state
    setActiveCatalog(document.getElementById("tab-bolsas") || catalogTabs[0]);
  }

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
        validate: (value) => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value.trim()),
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

      // Validar honeypot (anti-spam)
      const honeypot = form.querySelector('[name="_honey"]');
      if (honeypot && honeypot.value !== '') {
        // Es un bot, no enviar
        return false;
      }

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

      // Deshabilitar botón y mostrar loading
      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = "Enviando...";
      formStatus.textContent = "Enviando solicitud...";

      try {
        const response = await fetch("https://formsubmit.co/ajax/ventas@art4hotel.com", {
          method: "POST",
          body: new FormData(form),
          headers: {
            Accept: "application/json",
          },
        });

        if (response.status === 429) {
          throw new Error("Demasiadas solicitudes. Intenta en unos minutos.");
        }
        if (!response.ok) {
          throw new Error("Error del servidor. Intenta más tarde.");
        }

        formStatus.textContent = "✓ Solicitud enviada exitosamente. Te contactaremos pronto.";
        formStatus.style.color = "var(--olive-dark)";
        form.reset();
        submitBtn.disabled = false;
        submitBtn.textContent = "Solicitar Cotización";
      } catch (error) {
        formStatus.textContent = error.message || "No se pudo enviar. Intentando método alternativo...";
        formStatus.style.color = "#a23225";
        submitBtn.disabled = false;
        submitBtn.textContent = "Solicitar Cotización";

        // Fallback a envío normal si falla AJAX
        setTimeout(() => {
          form.submit();
        }, 2000);
      }
    });
  }
});
