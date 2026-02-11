const projects = [
  {
    title: "Tameable Beasts", desc: "Mod that adds more tameable mobs.", link: "tb_lore.html",
    img: "./assets/images/tb_logo.png", color: "tb-text",
    tags: ["Mod", "Forge", "NeoForge", "1.20.1"]
  },

  {
    title: "The Digimod", desc: "Mod that ports Digimon into Minecraft.", link: "td_lore.html",
    img: "./assets/images/td_logo.png", color: "td-text",
    tags: ["Mod", "Forge", "NeoForge", "1.20.1"]
  },

  {
    title: "Model Portfolio", desc: "Compilation of my best 3D Blockbench assets.", link: "portfolio.html",
    img: "./assets/images/p_logo.png", color: "p-text",
    tags: ["Art Collection"]
  },

  {
    title: "Companions!", desc: "Mod that adds tameable mobs and a boss.", link: "https://www.curseforge.com/minecraft/mc-mods/companions-mod",
    img: "./assets/images/co_logo.png", color: "co-text",
    tags: ["Mod", "Forge", "NeoForge", "Fabric", "1.20 - 1.21.1"]
  },

  {
    title: "Digimod [Cobblemon]", desc: "Addon that brings Digimod into Cobblemon.", link: "txc_lore.html",
    img: "./assets/images/txc_logo.png", color: "txc-text",
    tags: ["Mod", "Addon", "Forge", "NeoForge", "1.20.1"]
  },

  {
    title: "P.E.K.K.A. Craft", desc: "Mc mod that adds tameable P.E.K.K.A.s", link: "pk_lore.html",
    img: "./assets/images/pk_logo.png", color: "pk-text",
    tags: ["Mod", "Forge", "NeoForge", "Bedrock", "1.20.1"]
  },

  {
    title: "Animights", desc: "Mod that adds tameable loyal squires.", link: "animights_lore.html",
    img: "./assets/images/am_logo.png", color: "am-text",
    tags: ["Mod", "Forge", "NeoForge", "1.20.1"]
  },

  {
    title: "More Golems", desc: "Mod that adds more vanilla styled golems.", link: "mgolems_lore.html",
    img: "./assets/images/more_golems.png", color: "mg-text",
    tags: ["Mod", "Forge", "NeoForge", "1.20.1"]
  },

  {
    title: "????", desc: "??????<br>??????", link: "index.html",
    img: "./assets/images/unknown_logo.png", color: "td-text",
    tags: ["Mod"]
  }
];


const projectsContainer = document.getElementById("projects-container");
const filterBtn = document.getElementById("filter-btn");
const closeFilterBtn = document.getElementById("close-filter-btn");
const clearFiltersBtn = document.getElementById("clear-filters-btn");
const filterPanel = document.getElementById("filter-panel");
const filterOverlay = document.getElementById("filter-overlay");
const filterTagsContainer = document.getElementById("filter-tags-container");

function renderProjects(projectsToRender) {
  projectsContainer.innerHTML = projectsToRender.map(p => `
    <a href="${p.link}" class="secondary-button project-button">
      <div class="project-top-row">
        <div class="project-image-box">
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
}

function getUniqueTags() {
  const tags = new Set();
  projects.forEach(p => p.tags.forEach(tag => tags.add(tag)));
  return Array.from(tags).sort();
}

function renderFilterTags() {
  const tags = getUniqueTags();
  filterTagsContainer.innerHTML = tags.map(tag => `
    <div class="filter-tag ${selectedTags.has(tag) ? 'active' : ''}" data-tag="${tag}">
      ${tag}
    </div>
  `).join('');

  document.querySelectorAll('.filter-tag').forEach(tagElem => {
    tagElem.addEventListener('click', () => {
      const tag = tagElem.dataset.tag;
      toggleTag(tag);
    });
  });
}

function toggleTag(tag) {
  if (selectedTags.has(tag)) {
    selectedTags.delete(tag);
  } else {
    selectedTags.add(tag);
  }

  renderFilterTags();
  filterProjects();
}

function filterProjects() {
  if (selectedTags.size === 0) {
    renderProjects(projects);
  } else {
    const filtered = projects.filter(p => {
      return p.tags.some(tag => selectedTags.has(tag));
    });
    renderProjects(filtered);
  }
}

function openFilter() {
  filterPanel.classList.remove('translate-x-full');
  filterOverlay.classList.remove('hidden');
  setTimeout(() => {
    filterOverlay.classList.remove('opacity-0');
  }, 10);
  document.body.style.overflow = 'hidden';
}

function closeFilter() {
  filterPanel.classList.add('translate-x-full');
  filterOverlay.classList.add('opacity-0');
  setTimeout(() => {
    filterOverlay.classList.add('hidden');
  }, 300);
  document.body.style.overflow = '';
}

function clearFilters() {
  selectedTags.clear();
  renderFilterTags();
  filterProjects();
}

filterBtn.addEventListener('click', openFilter);
closeFilterBtn.addEventListener('click', closeFilter);
filterOverlay.addEventListener('click', closeFilter);
clearFiltersBtn.addEventListener('click', clearFilters);

renderProjects(projects);
renderFilterTags();
