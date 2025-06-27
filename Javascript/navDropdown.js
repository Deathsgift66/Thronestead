// Project Name: Thronestead©
// File Name: navDropdown.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
document.addEventListener("DOMContentLoaded", () => {
  const allDropdowns = document.querySelectorAll(".dropdown");

  allDropdowns.forEach((dropdown, index) => {
    const toggle = dropdown.querySelector(".dropdown-toggle");

    if (!toggle) return;

    // Set accessibility roles
    toggle.setAttribute("aria-haspopup", "true");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", `dropdown-menu-${index}`);

    const menu = dropdown.querySelector(".dropdown-menu");
    if (menu) {
      menu.setAttribute("role", "menu");
      menu.id = `dropdown-menu-${index}`;

      // Make menu items focusable
      const items = menu.querySelectorAll('[role="menuitem"]');
      items.forEach((item) => item.setAttribute('tabindex', '0'));

      // Trap focus within the menu
      menu.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && items.length > 0) {
          const first = items[0];
          const last = items[items.length - 1];

          if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          } else if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else if (e.key === 'Escape') {
          dropdown.classList.remove('show');
          toggle.setAttribute('aria-expanded', 'false');
          toggle.focus();
        }
      });
    }

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const isOpen = dropdown.classList.contains("show");

      // Close all other dropdowns
      allDropdowns.forEach((d) => {
        d.classList.remove("show");
        const t = d.querySelector(".dropdown-toggle");
        if (t) t.setAttribute("aria-expanded", "false");
      });

      // Toggle this one
      if (!isOpen) {
        dropdown.classList.add("show");
        toggle.setAttribute("aria-expanded", "true");
        const firstItem = dropdown
          .querySelector('.dropdown-menu [role="menuitem"]');
        if (firstItem) firstItem.focus();
      }
    });
  });

  // Close on outside click
  document.addEventListener("click", (e) => {
    allDropdowns.forEach((dropdown) => {
      if (!dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
        const toggle = dropdown.querySelector(".dropdown-toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
      }
    });
  });

  // Close all on ESC key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      allDropdowns.forEach((dropdown) => {
        dropdown.classList.remove("show");
        const toggle = dropdown.querySelector(".dropdown-toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
      });
    }
  });
});
