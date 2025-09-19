const projects = [
  { title: "Tameable Beasts", desc: "Mc mod that adds tameable mobs.", link: "tb_lore.html", 
    img: "./assets/images/tb_logo.png", color:"tb-text", w:2},
  
  { title: "The Digimod", desc: "Mc mod that adds digital creatures to raise.", link: "#", 
    img: "./assets/images/td_logo.png", color:"td-text", w:4.5},
  
  { title: "Model Portfolio", desc: "Compilation of my best Mc assets.", link: "portfolio.html", 
    img: "./assets/images/p_logo.png", color:"p-text", w:3}
];


document.getElementById("projects-container").innerHTML = projects.map(p => `
<a href="${p.link}" class="p-5 base-secondary-hoverable relative rounded-lg">
  <div class="flex items-center gap-4 mb-10">
    <img src="${p.img}" alt="${p.title}" style="width: ${p.w}rem; height: auto;">

    <span class="font-bold truncate leading-normal ${p.color} mt-5" style="font-size: 3.5vh;">
      ${p.title}
    </span>
  </div>

  <p class="absolute left-0 bottom-5 truncate leading-normal w-full px-5" style="font-size: 1.8vh;">
      ${p.desc}
  </p>
</a>


`).join('');
