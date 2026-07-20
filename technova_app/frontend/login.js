lucide.createIcons();

const canvas = document.getElementById('networkCanvas');
const ctx = canvas.getContext('2d');
let particlesArray;

canvas.width = window.innerWidth; 
canvas.height = window.innerHeight;

window.addEventListener('resize', () => { 
    canvas.width = window.innerWidth; 
    canvas.height = window.innerHeight; 
    init(); 
});

let mouse = { x: null, y: null, radius: 120 };
window.addEventListener('mousemove', (event) => { mouse.x = event.x; mouse.y = event.y; });
window.addEventListener('mouseout', () => { mouse.x = undefined; mouse.y = undefined; });

class Particle {
    constructor(x, y, directionX, directionY, size) {
        this.x = x; this.y = y; this.directionX = directionX; this.directionY = directionY; this.size = size;
    }
    draw() {
        ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
        ctx.fillStyle = '#4B0082'; ctx.fill();
    }
    update() {
        if (this.x > canvas.width || this.x < 0) this.directionX = -this.directionX;
        if (this.y > canvas.height || this.y < 0) this.directionY = -this.directionY;
        
        let dx = mouse.x - this.x; 
        let dy = mouse.y - this.y; 
        let distance = Math.sqrt(dx*dx + dy*dy);
        
        if (distance < mouse.radius + this.size) {
            if (mouse.x < this.x && this.x < canvas.width - this.size * 10) this.x += 2;
            if (mouse.x > this.x && this.x > this.size * 10) this.x -= 2;
            if (mouse.y < this.y && this.y < canvas.height - this.size * 10) this.y += 2;
            if (mouse.y > this.y && this.y > this.size * 10) this.y -= 2;
        }
        this.x += this.directionX; this.y += this.directionY; this.draw();
    }
}

function init() {
    particlesArray = []; 
    let numberOfParticles = (canvas.height * canvas.width) / 15000;
    for (let i = 0; i < numberOfParticles; i++) {
        let size = (Math.random() * 2) + 1;
        let x = (Math.random() * ((innerWidth - size * 2) - (size * 2)) + size * 2);
        let y = (Math.random() * ((innerHeight - size * 2) - (size * 2)) + size * 2);
        let directionX = (Math.random() * 1) - 0.5; let directionY = (Math.random() * 1) - 0.5;
        particlesArray.push(new Particle(x, y, directionX, directionY, size));
    }
}

function connect() {
    for (let a = 0; a < particlesArray.length; a++) {
        for (let b = a; b < particlesArray.length; b++) {
            let distance = ((particlesArray[a].x - particlesArray[b].x) * (particlesArray[a].x - particlesArray[b].x)) + ((particlesArray[a].y - particlesArray[b].y) * (particlesArray[a].y - particlesArray[b].y));
            if (distance < (canvas.width / 8) * (canvas.height / 8)) {
                let opacityValue = 1 - (distance / 20000);
                ctx.strokeStyle = 'rgba(75, 0, 130,' + opacityValue + ')'; 
                ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(particlesArray[a].x, particlesArray[a].y); ctx.lineTo(particlesArray[b].x, particlesArray[b].y); ctx.stroke();
            }
        }
    }
}

function animate() {
    requestAnimationFrame(animate); 
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    for (let i = 0; i < particlesArray.length; i++) particlesArray[i].update();
    connect();
}

init(); 
animate();



// LÓGICA DE LOGIN
const loginForm = document.getElementById('loginForm');
const loginView = document.getElementById('loginView');
const successView = document.getElementById('successView');
const successIcon = document.getElementById('successIcon');
const errorBox = document.getElementById('errorBox');
const errorMsg = document.getElementById('errorMsg');
const btnSubmit = document.getElementById('btnSubmit');

loginForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Limpiar errores previos y cambiar estado del botón
    errorBox.classList.remove('active');
    const btnOriginalText = btnSubmit.innerHTML;
    btnSubmit.innerHTML = '<i data-lucide="loader" class="spin"></i> Verificando...';
    lucide.createIcons();
    
    // Preparar datos para el servidor
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    // Enviar petición al backend en Python
    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            // Ocultar formulario suavemente (Animación)
            loginView.style.opacity = '0';
            setTimeout(() => {
                loginView.style.display = 'none';
                successView.classList.add('active');
                setTimeout(() => {
                    successIcon.classList.add('done');
                    successView.classList.add('done');
                    
                    // Redirigir a admin.html
                    setTimeout(() => {
                        window.location.href = 'admin.html';
                    }, 1000);
                    
                }, 800);
                
            }, 400);

        } else {
            // Mostrar error de credenciales
            errorMsg.textContent = data.message;
            errorBox.classList.add('active');
            btnSubmit.innerHTML = btnOriginalText;
            lucide.createIcons();
        }
    })
    .catch(error => {
        // Mostrar error de conexión/servidor
        errorMsg.textContent = "Servidor No Disponible. Intente Más Tarde.";
        errorBox.classList.add('active');
        btnSubmit.innerHTML = btnOriginalText;
        lucide.createIcons();
    });
});