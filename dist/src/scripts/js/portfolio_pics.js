const pics = [
    { img: "allay_mage.png" },
    { img: "antlion.png" },
    { img: "chikote.png" },
    { img: "cornelius_croak.png" },
    { img: "croissant_dragon.png" },
    { img: "cultist.png" },
    { img: "illager_golem.png" },
    { img: "lib.png" },
    { img: "minions.png" },
    { img: "penguin.png" },
    { img: "pinocchi.png" },
    { img: "pontiff.png" },
    { img: "racoon.png" },
    { img: "sword_shade.png" },
    { img: "quadruped_shade.png" },
    { img: "roly_poly.png" },
    { img: "teddy.png" },
    { img: "shiny_beetle.png" },
    { img: "ground_beetle.png" },
    { img: "quetzal.png" },
    { img: "scarecrow.png" },
    { img: "graptera.png" },
    { img: "argentavis.png" },
    { img: "minipk.png" },
    { img: "pekka.png" },
    { img: "cactus_golem.png" },
    { img: "gold_golem.png" },
    { img: "castle_golem.png" }
];

let lightbox;
let lightboxImg;

function initLightbox() {
    if (lightbox) {
        return;
    }

    lightbox = document.createElement("div");
    lightbox.className = "portfolio-lightbox";
    lightbox.innerHTML = `
        <button class="portfolio-lightbox-close" type="button" aria-label="Close image">x</button>
        <img alt="Enlarged portfolio artwork">
    `;

    lightboxImg = lightbox.querySelector("img");
    const closeBtn = lightbox.querySelector(".portfolio-lightbox-close");

    function closeLightbox() {
        lightbox.classList.remove("open");
        document.body.style.overflow = "";
    }

    lightbox.addEventListener("click", (event) => {
        if (event.target === lightbox) {
            closeLightbox();
        }
    });

    closeBtn.addEventListener("click", closeLightbox);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && lightbox.classList.contains("open")) {
            closeLightbox();
        }
    });

    document.body.appendChild(lightbox);
}

function openLightbox(src, alt) {
    if (!lightbox || !lightboxImg) {
        return;
    }

    lightboxImg.src = src;
    lightboxImg.alt = alt;
    lightbox.classList.add("open");
    document.body.style.overflow = "hidden";
}

function renderPics() {
    const container = document.getElementById("pics-container");
    const cols = window.innerWidth < 768 ? 1 : window.innerWidth < window.innerHeight ? 2 : 4;
    const gap = 11;
    const containerWidth = Math.max(container.clientWidth, 320);
    const size = Math.floor((containerWidth - (cols - 1) * gap) / cols);

    container.innerHTML = pics.map(p => `
    <div class="inline-block rounded w-fit">
        <div class="flex items-center">
            <img src="./src/assets/images/portfolio/${p.img}" alt="${p.img.replace(/\.[^.]+$/, "").replace(/_/g, " ")}" class="portfolio-thumb" style="width:${size}px; height:${size}px;">
        </div>
    </div>
    `).join('');

    container.querySelectorAll(".portfolio-thumb").forEach((img) => {
        img.addEventListener("click", () => {
            openLightbox(img.src, img.alt);
        });
    });
}

initLightbox();
renderPics();
window.addEventListener("resize", renderPics);