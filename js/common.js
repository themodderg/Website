const navbarHTML = `
<nav class="bg-secondary-selected top-section bg-secondary-selected" >
  <h1 class="font-bold" style="font-size: 4vh;">
      <a href="index.html" class="hover:underline hover:text-special">G's Lore</a>
  </h1>

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
