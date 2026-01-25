const projects = [
  { title: "Tameable Beasts", desc: "Mod that adds more tameable mobs.", link: "tb_lore.html", 
    img: "./assets/images/tb_logo.png", color:"tb-text"},
  
  { title: "The Digimod", desc: "Mod that ports Digimon into Minecraft.", link: "td_lore.html", 
    img: "./assets/images/td_logo.png", color:"td-text"},
  
  { title: "Model Portfolio", desc: "Compilation of my best 3D Blockbench assets.", link: "portfolio.html", 
    img: "./assets/images/p_logo.png", color:"p-text"},
  
  { title: "Companions!", desc: "Mod that adds tameable mobs and a boss.", link: "https://www.curseforge.com/minecraft/mc-mods/companions-mod", 
    img: "./assets/images/co_logo.png", color:"co-text"},
  
  { title: "Digimod [Cobblemon]", desc: "Addon that brings Digimod into Cobblemon.", link: "txc_lore.html", 
    img: "./assets/images/txc_logo.png", color:"txc-text"},
  
  { title: "P.E.K.K.A. Craft", desc: "Mc mod that adds tameable P.E.K.K.A.s", link: "pk_lore.html", 
    img: "./assets/images/pk_logo.png", color:"pk-text"},
  
  { title: "Animights", desc: "Mod that adds tameable loyal squires.", link: "https://www.curseforge.com/minecraft/mc-mods/animights", 
    img: "./assets/images/am_logo.png", color:"am-text"},
  
  { title: "More Golems", desc: "Mod that adds more vanilla styled golems.", link: "mgolems_lore.html", 
    img: "./assets/images/more_golems.png", color:"mg-text"},
  
  { title: "????", desc: "??????<br>??????", link: "index.html", 
    img: "./assets/images/unknown_logo.png", color:"td-text"}
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
