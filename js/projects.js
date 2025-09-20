const projects = [
  { title: "Tameable Beasts", desc: "Mc mod that adds new tameable mobs to the world.", link: "tb_lore.html", 
    img: "./assets/images/tb_logo.png", color:"tb-text", w:2},
  
  { title: "The Digimod", desc: "Mc mod that adds digital creatures to raise to the world.", link: "#", 
    img: "./assets/images/td_logo.png", color:"td-text", w:4.5},
  
  { title: "Model Portfolio", desc: "Compilation of my best 3D Blockbench assets.", link: "portfolio.html", 
    img: "./assets/images/p_logo.png", color:"p-text", w:3}
];


document.getElementById("projects-container").innerHTML = projects.map(p => `
<a href="${p.link}" class="base-secondary-hoverable project-button">
  <div class="project-image-box">
    <img src="${p.img}" alt="${p.title}" class="project-image">
  </div>

  <div>
    <span class="project-title ${p.color}">${p.title}</span>
    <div class="project-title secondary-selected-line"></div>
    <p class="project-desc">${p.desc}</p>
  </div>
</a>

`).join('');
