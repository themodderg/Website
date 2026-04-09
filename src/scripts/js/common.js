const navbarHTML = `
<nav class="top-section" >

  <div class="nav-left-group">
    <button id="sidebar-toggle-btn" class="sidebar-toggle-btn" type="button" aria-label="Open navigation sidebar" aria-expanded="false" aria-controls="site-sidebar-panel">
      <i class="fa-solid fa-bars"></i>
    </button>

    <a href="index.html">
        <img src="./src/assets/images/logo.png" 
          alt="CodderG" 
          style="height: 42px; width: auto;" 
          class="object-contain hover:opacity-80">
    </a>
  </div>

  <div class="flex space-x-4 items-center text-xl">
    <a href="https://x.com/themodderG" target="_blank" rel="noopener noreferrer" class="social-link hover:text-blue-400" aria-label="Twitter">
      <i class="fa-brands fa-twitter"></i>
    </a>

    <a href="https://github.com/ginerJ" target="_blank" rel="noopener noreferrer" class="social-link hover:text-purple-400" aria-label="GitHub">
      <i class="fa-brands fa-github"></i>
    </a>

    <a href="https://www.youtube.com/@TheModderG" target="_blank" rel="noopener noreferrer" class="social-link hover:text-red-400" aria-label="YouTube">
      <i class="fa-brands fa-youtube"></i>
    </a>

    <a href="https://www.instagram.com/themodderg/" target="_blank" rel="noopener noreferrer" class="social-link hover:text-pink-400" aria-label="Instagram">
      <i class="fa-brands fa-instagram"></i>
    </a>

    <a href="https://www.tumblr.com/blog/themodderg" target="_blank" rel="noopener noreferrer" class="social-link hover:text-pink-400" aria-label="Tumblr">
      <i class="fa-brands fa-tumblr"></i>
    </a>

    <a href="https://www.deviantart.com/modderg" target="_blank" rel="noopener noreferrer" class="social-link hover:text-green-400" aria-label="DeviantArt">
      <i class="fa-brands fa-deviantart"></i>
    </a>

    <a href="https://www.fiverr.com/modderg" target="_blank" rel="noopener noreferrer" class="social-link fiverr-link" aria-label="Fiverr">
      <img src="./src/assets/images/fiverr_logo.png" 
        alt="Fiverr" 
        style="height: 1.25rem; width: auto;" 
        class="object-contain">
    </a>

    <a href="https://discord.gg/EeNkjGZY37" target="_blank" rel="noopener noreferrer" class="social-link hover:text-indigo-500" aria-label="Discord">
      <i class="fa-brands fa-discord"></i>
    </a>
  </div>
</nav>

<div id="site-sidebar-overlay" class="site-sidebar-overlay" aria-hidden="true"></div>

<aside id="site-sidebar-panel" class="site-sidebar-panel" aria-hidden="true" role="dialog" aria-label="Site navigation sidebar">
  <div class="site-sidebar-header">
    <h3 class="font-bold" style="font-size: 1.2rem;">Explore</h3>
    <button id="sidebar-close-btn" class="site-sidebar-close" type="button" aria-label="Close navigation sidebar">
      <i class="fa-solid fa-xmark"></i>
    </button>
  </div>

  <div class="site-sidebar-content">
    <section class="site-sidebar-section">
      <button class="site-sidebar-section-toggle" type="button" aria-expanded="false">
        <span class="site-sidebar-title">Socials</span>
        <i class="fa-solid fa-chevron-down"></i>
      </button>
      <div class="site-sidebar-links" hidden>
        <a class="site-sidebar-social site-sidebar-social-twitter" href="https://x.com/themodderG" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-twitter"></i><span>Twitter / X</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-github" href="https://github.com/ginerJ" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-github"></i><span>GitHub</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-youtube" href="https://www.youtube.com/@TheModderG" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-youtube"></i><span>YouTube</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-instagram" href="https://www.instagram.com/themodderg/" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-instagram"></i><span>Instagram</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-tumblr" href="https://www.tumblr.com/blog/themodderg" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-tumblr"></i><span>Tumblr</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-deviantart" href="https://www.deviantart.com/modderg" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-deviantart"></i><span>DeviantArt</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-fiverr" href="https://www.fiverr.com/s/m5r7qZV" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><img class="site-sidebar-fiverr-icon" src="./src/assets/images/fiverr_logo.png" alt=""><span>Fiverr</span></span>
        </a>
        <a class="site-sidebar-social site-sidebar-social-discord" href="https://discord.gg/EeNkjGZY37" target="_blank" rel="noopener noreferrer">
          <span class="site-sidebar-social-row"><i class="fa-brands fa-discord"></i><span>Discord</span></span>
        </a>
      </div>
    </section>

    <section class="site-sidebar-section">
      <button class="site-sidebar-section-toggle" type="button" aria-expanded="false">
        <span class="site-sidebar-title">Mods</span>
        <i class="fa-solid fa-chevron-down"></i>
      </button>
      <div class="site-sidebar-links" hidden>
        <a class="site-sidebar-project site-sidebar-project-td" href="td_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/td_logo.png" alt=""><span>The Digimod</span></span>
        </a>
        <a class="site-sidebar-project site-sidebar-project-mg" href="mgolems_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/more_golems.png" alt=""><span>More Golems</span></span>
        </a>
        <a class="site-sidebar-project site-sidebar-project-am" href="animights_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/am_logo.png" alt=""><span>Animights</span></span>
        </a>
        <a class="site-sidebar-project site-sidebar-project-tb" href="tb_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/tb_logo.png" alt=""><span>Tameable Beasts</span></span>
        </a>
        <a class="site-sidebar-project site-sidebar-project-pk" href="pk_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/pk_logo.png" alt=""><span>PEKKA Craft</span></span>
        </a>
      </div>
    </section>

    <section class="site-sidebar-section">
      <button class="site-sidebar-section-toggle" type="button" aria-expanded="false">
        <span class="site-sidebar-title">Bedrock Add-Ons</span>
        <i class="fa-solid fa-chevron-down"></i>
      </button>
      <div class="site-sidebar-links" hidden>
        <a class="site-sidebar-project site-sidebar-project-pk" href="pk_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/pk_logo.png" alt=""><span>PEKKA Craft</span></span>
        </a>
      </div>
    </section>

    <section class="site-sidebar-section">
      <button class="site-sidebar-section-toggle" type="button" aria-expanded="false">
        <span class="site-sidebar-title">Mod Add-Ons</span>
        <i class="fa-solid fa-chevron-down"></i>
      </button>
      <div class="site-sidebar-links" hidden>
        <a class="site-sidebar-project site-sidebar-project-txc" href="txc_lore.html">
          <span class="site-sidebar-project-row"><img class="site-sidebar-project-icon" src="./src/assets/images/txc_logo.png" alt=""><span>The Digimod [Cobblemon]</span></span>
        </a>
      </div>
    </section>
  </div>
</aside>
`;

const footerHTML = `
<footer class="text-center text-sm text-secondary-selected p-10 bg-secondary">
  © 2026 
  <a href="index.html" class="underline hover:text-white">CodderG</a>
  ·
  <a href="privacy-policy.html" class="underline hover:text-white">Privacy Policy</a>
</footer>
`;

document.body.insertAdjacentHTML("beforeend", footerHTML);
document.body.insertAdjacentHTML("afterbegin", navbarHTML);

const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
const sidebarCloseBtn = document.getElementById("sidebar-close-btn");
const siteSidebarPanel = document.getElementById("site-sidebar-panel");
const siteSidebarOverlay = document.getElementById("site-sidebar-overlay");

function openSiteSidebar() {
  if (!siteSidebarPanel || !siteSidebarOverlay) {
    return;
  }

  siteSidebarPanel.classList.add("open");
  siteSidebarOverlay.classList.add("open");
  siteSidebarPanel.setAttribute("aria-hidden", "false");
  siteSidebarOverlay.setAttribute("aria-hidden", "false");

  if (sidebarToggleBtn) {
    sidebarToggleBtn.setAttribute("aria-expanded", "true");
  }
}

function closeSiteSidebar() {
  if (!siteSidebarPanel || !siteSidebarOverlay) {
    return;
  }

  siteSidebarPanel.classList.remove("open");
  siteSidebarOverlay.classList.remove("open");
  siteSidebarPanel.setAttribute("aria-hidden", "true");
  siteSidebarOverlay.setAttribute("aria-hidden", "true");

  if (sidebarToggleBtn) {
    sidebarToggleBtn.setAttribute("aria-expanded", "false");
  }
}

if (sidebarToggleBtn) {
  sidebarToggleBtn.addEventListener("click", openSiteSidebar);
}

if (sidebarCloseBtn) {
  sidebarCloseBtn.addEventListener("click", closeSiteSidebar);
}

if (siteSidebarOverlay) {
  siteSidebarOverlay.addEventListener("click", closeSiteSidebar);
}

if (siteSidebarPanel) {
  siteSidebarPanel.querySelectorAll(".site-sidebar-section-toggle").forEach((toggleBtn) => {
    toggleBtn.addEventListener("click", () => {
      const section = toggleBtn.closest(".site-sidebar-section");
      if (!section) {
        return;
      }

      const links = section.querySelector(".site-sidebar-links");
      if (!links) {
        return;
      }

      const isExpanded = toggleBtn.getAttribute("aria-expanded") === "true";
      const nextExpanded = !isExpanded;

      toggleBtn.setAttribute("aria-expanded", String(nextExpanded));
      links.hidden = !nextExpanded;
      section.classList.toggle("expanded", nextExpanded);
    });
  });

  siteSidebarPanel.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeSiteSidebar);
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeSiteSidebar();
  }
});

function syncAdPlaceholderTint() {
  const hosts = document.querySelectorAll(".ad-inner, .mobile-ad-slot");

  hosts.forEach((host) => {
    const ad = host.querySelector(".adsbygoogle");
    if (!ad) {
      return;
    }

    const status = (ad.getAttribute("data-ad-status") || "").toLowerCase();
    const isFilled = status === "filled";

    host.classList.toggle("ad-filled", isFilled);
  });
}

function watchAdPlaceholderTint() {
  const adNodes = document.querySelectorAll(".adsbygoogle");
  if (adNodes.length === 0) {
    return;
  }

  const observer = new MutationObserver(() => {
    syncAdPlaceholderTint();
  });

  adNodes.forEach((ad) => {
    observer.observe(ad, {
      attributes: true,
      attributeFilter: ["data-ad-status"],
      childList: true,
      subtree: true,
    });
  });

  syncAdPlaceholderTint();
  window.addEventListener("load", syncAdPlaceholderTint);
  window.addEventListener("pageshow", syncAdPlaceholderTint);
  setTimeout(syncAdPlaceholderTint, 1000);
  setTimeout(syncAdPlaceholderTint, 2500);
  setTimeout(syncAdPlaceholderTint, 5000);
  setTimeout(syncAdPlaceholderTint, 8000);
}

function syncDesktopAdRails() {
  const desktopLandscape = window.matchMedia("(min-width: 1280px) and (orientation: landscape)").matches;
  const sidebars = document.querySelectorAll(".ad-sidebar");

  sidebars.forEach((sidebar) => {
    const sticky = sidebar.querySelector(".ad-sticky");
    if (!sticky) {
      return;
    }

    if (!desktopLandscape) {
      sidebar.style.display = "none";
      sticky.style.position = "sticky";
      sticky.style.top = "0";
      sticky.style.left = "";
      sticky.style.width = "100%";
      sticky.style.height = "100vh";
      return;
    }

    sidebar.style.display = "flex";

    const rect = sidebar.getBoundingClientRect();
    sticky.style.position = "fixed";
    sticky.style.top = "0";
    sticky.style.left = `${Math.round(rect.left)}px`;
    sticky.style.width = `${Math.round(rect.width)}px`;
    sticky.style.height = "100vh";
  });
}

syncDesktopAdRails();
window.addEventListener("resize", syncDesktopAdRails);
watchAdPlaceholderTint();
