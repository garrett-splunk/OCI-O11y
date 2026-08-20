(function () {
  const STORAGE_KEY = "splunk-workshop-theme";
  const toast = document.getElementById("toast");
  const navLinks = document.querySelectorAll(".sidebar-tree__link[data-step]");
  const progressBar = document.getElementById("progressBar");
  const themeToggle = document.getElementById("themeToggle");
  const html = document.documentElement;

  /* ---- Theme (light / dark / auto) ---- */
  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(mode) {
    const resolved = mode === "auto" ? getSystemTheme() : mode;
    html.setAttribute("data-theme", resolved);
    html.setAttribute("data-theme-mode", mode);
    if (themeToggle) {
      themeToggle.setAttribute(
        "aria-label",
        mode === "dark" ? "Switch to light mode" : mode === "light" ? "Switch to dark mode" : "Theme: auto (system)"
      );
    }
  }

  function cycleTheme() {
    const order = ["auto", "light", "dark"];
    const current = localStorage.getItem(STORAGE_KEY) || "auto";
    const next = order[(order.indexOf(current) + 1) % order.length];
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  const saved = localStorage.getItem(STORAGE_KEY) || "auto";
  applyTheme(saved);

  if (themeToggle) themeToggle.addEventListener("click", cycleTheme);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem(STORAGE_KEY) || "auto") === "auto") applyTheme("auto");
  });

  /* ---- Copy buttons ---- */
  document.querySelectorAll(".btn-copy").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-copy");
      const el = document.getElementById(id);
      if (!el) return;
      const text = el.textContent.trim();
      try {
        await navigator.clipboard.writeText(text);
        showToast("Copied to clipboard");
      } catch {
        showToast("Select and copy manually");
      }
    });
  });

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2000);
  }

  /* ---- Sidebar active section ---- */
  const sections = [...navLinks]
    .map((link) => {
      const id = link.getAttribute("href")?.slice(1);
      const section = id ? document.getElementById(id) : null;
      return section ? { link, section } : null;
    })
    .filter(Boolean);

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const match = sections.find((s) => s.section === entry.target);
          if (match) setActive(match.link);
        }
      });
    },
    { rootMargin: "-22% 0px -58% 0px", threshold: 0 }
  );

  sections.forEach(({ section }) => observer.observe(section));

  function setActive(activeLink) {
    navLinks.forEach((l) => {
      const on = l === activeLink;
      l.classList.toggle("is-active", on);
      l.setAttribute("aria-current", on ? "true" : "false");
    });
    const tocLinks = document.querySelectorAll(".toc__link");
    tocLinks.forEach((l) => l.classList.remove("is-active"));
  }

  if (sections.length) setActive(sections[0].link);

  /* ---- On-this-page TOC ---- */
  const tocNav = document.getElementById("tocNav");
  if (tocNav) {
    const headings = document.querySelectorAll(".prose h2, .prose h3");
    headings.forEach((h) => {
      if (!h.id) h.id = h.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
      const a = document.createElement("a");
      a.href = `#${h.id}`;
      a.className = `toc__link toc__link--${h.tagName.toLowerCase()}`;
      a.textContent = h.textContent;
      tocNav.appendChild(a);
    });

    const tocObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            document.querySelectorAll(".toc__link").forEach((l) => {
              l.classList.toggle("is-active", l.getAttribute("href") === `#${id}`);
            });
          }
        });
      },
      { rootMargin: "-25% 0px -60% 0px", threshold: 0 }
    );
    headings.forEach((h) => tocObserver.observe(h));
  }

  /* ---- Reading progress ---- */
  function updateProgress() {
    if (!progressBar) return;
    const doc = document.documentElement;
    const scrollTop = doc.scrollTop || document.body.scrollTop;
    const height = doc.scrollHeight - doc.clientHeight;
    progressBar.style.width = height > 0 ? `${(scrollTop / height) * 100}%` : "0%";
  }
  window.addEventListener("scroll", updateProgress, { passive: true });
  updateProgress();
})();
