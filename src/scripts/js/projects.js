const projects = [
  {
    title: "Tameable Beasts", desc: "Mod that adds more tameable mobs.", link: "tb_lore.html",
    img: "./src/assets/images/tb_logo.png", hoverImg: "./src/assets/images/tameable_beasts/render.png", color: "tb-text",
    tags: ["Forge", "NeoForge", "1.20"]
  },

  {
    title: "The Digimod", desc: "Mod that ports Digimon into Minecraft.", link: "td_lore.html",
    img: "./src/assets/images/td_logo.png", hoverImg: "./src/assets/images/the_digimod/render.png", color: "td-text",
    tags: ["Forge", "NeoForge", "1.20"]
  },

  {
    title: "Model Portfolio", desc: "Compilation of my best 3D Blockbench assets.", link: "portfolio.html",
    img: "./src/assets/images/p_logo.png", hoverImg: "./src/assets/images/portfolio/render.png", color: "p-text",
    tags: ["Art Collection"]
  },

  {
    title: "Companions!", desc: "Mod that adds tameable mobs and a boss.", link: "https://www.curseforge.com/minecraft/mc-mods/companions-mod",
    img: "./src/assets/images/co_logo.png", hoverImg: "./src/assets/images/companions/render.png", color: "co-text",
    tags: ["Forge", "NeoForge", "Fabric", "1.20", "1.21", "MOTY"]
  },

  {
    title: "Digimod [Cobblemon]", desc: "Addon that brings Digimod into Cobblemon.", link: "txc_lore.html",
    img: "./src/assets/images/txc_logo.png", hoverImg: "./src/assets/images/digimodxcobblemon/render.png", color: "txc-text",
    tags: ["Forge", "NeoForge", "1.20"]
  },

  {
    title: "P.E.K.K.A. Craft", desc: "Mc mod that adds tameable P.E.K.K.A.s", link: "pk_lore.html",
    img: "./src/assets/images/pk_logo.png", hoverImg: "./src/assets/images/pk_craft/render.png", color: "pk-text",
    tags: ["Forge", "NeoForge", "Bedrock", "1.20"]
  },

  {
    title: "Animights", desc: "Mod that adds tameable loyal squires.", link: "animights_lore.html",
    img: "./src/assets/images/am_logo.png", hoverImg: "./src/assets/images/animights/render.png", color: "am-text",
    tags: ["Forge", "NeoForge", "1.20"]
  },

  {
    title: "More Golems", desc: "Mod that adds more vanilla styled golems.", link: "mgolems_lore.html",
    img: "./src/assets/images/more_golems.png", hoverImg: "./src/assets/images/more_golems/render.png", color: "mg-text",
    tags: ["Forge", "NeoForge", "1.20"]
  },

  {
    title: "????", desc: "??????<br>??????", link: "index.html",
    img: "./src/assets/images/unknown_logo.png", color: "td-text",
    tags: ["Forge", "NeoForge", "1.20"]
  }
];

const projectsContainer = document.getElementById("projects-container");

function attachProjectTagWheelScrolling() {
  document.querySelectorAll(".project-tags").forEach((tagsRow) => {
    tagsRow.addEventListener("wheel", (event) => {
      if (tagsRow.scrollWidth <= tagsRow.clientWidth) {
        return;
      }

      const delta = Math.abs(event.deltaY) > Math.abs(event.deltaX) ? event.deltaY : event.deltaX;
      if (delta === 0) {
        return;
      }

      event.preventDefault();
      tagsRow.scrollLeft += delta;
    }, { passive: false });
  });
}

function renderProjects(projectsToRender) {
  projectsContainer.innerHTML = projectsToRender.map(p => `
    <a href="${p.link}" class="secondary-button project-button">
      <div class="project-top-row">
        <div class="project-image-box">
          ${p.hoverImg ? `<img src="${p.hoverImg}" alt="" aria-hidden="true" class="project-hover-image">` : ''}
          <img src="${p.img}" alt="${p.title}" class="project-image">
        </div>

        <div style="flex:1 1 auto ;min-width:0;">
          <span class="project-title ${p.color}">${p.title}</span>
          <div class="secondary-selected-line"></div>
          <p class="project-desc">${p.desc}</p>
        </div>
      </div>

      <div class="project-tags">
        ${p.tags.map(tag => `<span class="project-tag">${tag}</span>`).join('')}
      </div>

    </a>
  `).join('');

  attachProjectTagWheelScrolling();
}

renderProjects(projects);
