const runners = [
    'teddy.gif',
    'racoon.gif',
    'mini_pk.gif',
    'sword.gif',
    'cactus_golem.gif',
    'agumon.gif'
];

function spawnRunner() {
    if (document.hidden) return;
    const container = document.querySelector('.hero-text');
    if (!container) return;

    const randomRunner = runners[Math.floor(Math.random() * runners.length)];

    const img = document.createElement('img');
    img.src = `src/assets/images/runners/${randomRunner}`;
    img.classList.add('hero-runner');
    img.alt = 'Runner Animation';

    container.appendChild(img);

    img.addEventListener('animationend', () => {
        img.remove();
    }, { once: true });
}

setTimeout(spawnRunner, 2000);

setInterval(spawnRunner, 20000);
