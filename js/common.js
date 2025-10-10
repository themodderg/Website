const navbarHTML = `
<nav class="top-section" >

  <a href="index.html">
      <img src="./assets/images/logo.png" 
        alt="Fiverr" 
        style="height: 5vh; width: auto;" 
        class="object-contain hover:opacity-80">
  </a>

  <div class="flex space-x-4 items-center">
    <a href="https://x.com/themodderG" target="_blank" class="hover:text-blue-400">
      <i class="fa-brands fa-twitter" style="font-size: 3vh;"></i>
    </a>

    <a href="https://github.com/ginerJ" target="_blank" class="hover:text-purple-400">
      <i class="fa-brands fa-github" style="font-size: 3vh;"></i>
    </a>

    <a href="https://www.youtube.com/@TheModderG" target="_blank" class="hover:text-red-400">
      <i class="fa-brands fa-youtube" style="font-size: 3vh;"></i>
    </a>

    <a href="https://www.fiverr.com/s/m5r7qZV" target="_blank">
      <img src="./assets/images/fiverr_logo.png" 
        alt="Fiverr" 
        style="height: 3vh; width: auto;" 
        class="object-contain hover:opacity-80">
    </a>

    <a href="https://discord.gg/EeNkjGZY37" target="_blank" class="hover:text-indigo-500">
      <i class="fa-brands fa-discord" style="font-size: 3vh;"></i>
    </a>
  </div>
</nav>
`;

const footerHTML = `
<footer class="text-center text-sm text-secondary-selected p-10 bg-secondary mt-auto">
  © 2025 <a href="#" class="underline hover:text-white">CodderG</a>
</footer>
`;

document.body.insertAdjacentHTML("beforeend", footerHTML);
document.body.insertAdjacentHTML("afterbegin", navbarHTML);
