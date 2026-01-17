const projects = [
  { title: "Tameable Beasts", desc: "Mc mod that adds new tameable mobs to the world.", link: "tb_lore.html", 
    img: "./assets/images/tb_logo.png", color:"tb-text"},
  
  { title: "The Digimod", desc: "Mc mod that ports the digimon franchise to the world.", link: "td_lore.html", 
    img: "./assets/images/td_logo.png", color:"td-text"},
  
  { title: "Model Portfolio", desc: "Compilation of my best 3D Blockbench assets.", link: "portfolio.html", 
    img: "./assets/images/p_logo.png", color:"p-text"},
  
  { title: "Companions!", desc: "Mc mod that adds creative tameable mobs and a boss fight.", link: "https://www.curseforge.com/minecraft/mc-mods/companions-mod", 
    img: "./assets/images/co_logo.png", color:"co-text"},
  
  { title: "Digimod [Cobblemon]", desc: "Mc addon that brings Digimon into the Cobblemon mod.", link: "txc_lore.html", 
    img: "./assets/images/txc_logo.png", color:"txc-text"},
  
  { title: "P.E.K.K.A. Craft", desc: "Mc mod that adds tameable P.E.K.K.A.s", link: "https://www.curseforge.com/minecraft/mc-mods/pk-craft", 
    img: "./assets/images/pk_logo.png", color:"pk-text"},
  
  { title: "Animights", desc: "Mc mod that adds anthropomorphic loyal squires.", link: "https://www.curseforge.com/minecraft/mc-mods/animights", 
    img: "./assets/images/am_logo.png", color:"am-text"},
  
  { title: "????", desc: "??????<br>??????", link: "index.html", 
    img: "./assets/images/unknown_logo.png", color:"td-text"},
  
  { title: "????", desc: "??????<br>??????", link: "index.html", 
    img: "./assets/images/unknown_logo3.png", color:"td-text"}
];
  

document.getElementById("projects-container").innerHTML = projects.map(p => `
<a href="${p.link}" class="secondary-button project-button">
  <div class="project-image-box">
    <img src="${p.img}" alt="${p.title}" class="project-image">
  </div>

  <div style="flex:1 1 auto ;min-width:0;">
    <span class="project-title ${p.color}">${p.title}</span>
    <div class="secondary-selected-line"></div>
    <p class="project-desc">${p.desc}</p>
  </div>

</a>

`).join('');
