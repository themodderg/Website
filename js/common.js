const navbarHTML = `
<nav class="top-section" >

  <a href="index.html">
      <img src="./assets/images/logo.png" 
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

    <a href="https://www.fiverr.com/s/m5r7qZV" target="_blank" rel="noopener noreferrer" class="social-link" aria-label="Fiverr">
      <img src="./assets/images/fiverr_logo.png" 
        alt="Fiverr" 
        style="height: 1.25rem; width: auto;" 
        class="object-contain hover:opacity-80">
    </a>

    <a href="https://discord.gg/EeNkjGZY37" target="_blank" rel="noopener noreferrer" class="social-link hover:text-indigo-500" aria-label="Discord">
      <i class="fa-brands fa-discord"></i>
    </a>
  </div>
</nav>
`;

const footerHTML = `
<footer class="text-center text-sm text-secondary-selected p-10 bg-secondary mt-auto">
  © 2026 
  <a href="index.html" class="underline hover:text-white">CodderG</a>
  ·
  <a href="privacy-policy.html" class="underline hover:text-white">Privacy Policy</a>
</footer>
`;

document.body.insertAdjacentHTML("beforeend", footerHTML);
document.body.insertAdjacentHTML("afterbegin", navbarHTML);
