const navbarHTML = `
<nav class="top-section" >

  <a href="index.html">
      <img src="./src/assets/images/logo.png" 
        alt="CodderG" 
        style="height: 42px; width: auto;" 
        class="object-contain hover:opacity-80">
  </a>

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
