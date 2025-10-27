const pics = [
  {img: "allay_mage.png"},
  {img: "antlion.png"},
  {img: "chikote.png"},
  {img: "cornelius_croak.png"},
  {img: "croissant_dragon.png"},
  {img: "cultist.png"},
  {img: "illager_golem.png"},
  {img: "lib.png"},
  {img: "minions.png"},
  {img: "penguin.png"},
  {img: "pinocchi.png"},
  {img: "pontiff.png"},
  {img: "racoon.png"},
  {img: "sword_shade.png"},
  {img: "quadruped_shade.png"},
  {img: "roly_poly.png"},
  {img: "teddy.png"},
  {img: "shiny_beetle.png"},
  {img: "ground_beetle.png"},
  {img: "quetzal.png"},
  {img: "scarecrow.png"},
  {img: "graptera.png"},
  {img: "argentavis.png"}
];

function renderPics() {
    const cols = window.innerWidth < window.innerHeight? 2:4;
    const gap = 11;
    const size = Math.floor((window.innerWidth - (cols-1) * gap) / cols);

    document.getElementById("pics-container").innerHTML = pics.map(p => `
    <div class="inline-block rounded w-fit">
        <div class="flex items-center">
            <img src="./assets/images/portfolio/${p.img}" style="width:${size}px; height:${size}px;">
        </div>
    </div>
    `).join('');
}

renderPics();
window.addEventListener("resize", renderPics);