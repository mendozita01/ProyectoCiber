lucide.createIcons();

// Animaciones on Scroll
const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
        }
    });
}, { threshold: 0.2 });

document.querySelectorAll('.slide-in-left, .slide-in-right').forEach(el => {
    scrollObserver.observe(el);
});

// Canvas Background Logic
const canvas = document.getElementById('networkCanvas');
const ctx = canvas.getContext('2d');
let particlesArray;

canvas.width = window.innerWidth; canvas.height = window.innerHeight;
window.addEventListener('resize', () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; init(); });

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
        let dx = mouse.x - this.x; let dy = mouse.y - this.y; let distance = Math.sqrt(dx*dx + dy*dy);
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
    particlesArray = []; let numberOfParticles = (canvas.height * canvas.width) / 15000;
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
    requestAnimationFrame(animate); ctx.clearRect(0, 0, innerWidth, innerHeight);
    for (let i = 0; i < particlesArray.length; i++) particlesArray[i].update();
    connect();
}
init(); animate();

// Logica del Modal
const modalOverlay = document.getElementById('modalOverlay');
const btnAbrirModal = document.getElementById('btnAbrirModal');
const btnCerrarModalX = document.getElementById('btnCerrarModalX');
const btnCancelarForm = document.getElementById('btnCancelarForm');
const btnCerrarExito = document.getElementById('btnCerrarExito');
const ticketForm = document.getElementById('ticketForm');
const formView = document.getElementById('formView');
const successView = document.getElementById('successView');

btnAbrirModal.addEventListener('click', () => {
    formView.style.display = 'block'; 
    successView.style.display = 'none';
    
    // Limpiar el mensaje de error si se vuelve a abrir el modal
    const errorMsgDiv = document.getElementById('formErrorMsg');
    if (errorMsgDiv) errorMsgDiv.style.display = 'none';

    ticketForm.reset(); 
    modalOverlay.classList.add('active');
});

const cerrarModal = () => { modalOverlay.classList.remove('active'); };
btnCerrarModalX.addEventListener('click', cerrarModal);
btnCancelarForm.addEventListener('click', cerrarModal);
btnCerrarExito.addEventListener('click', cerrarModal);
modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) cerrarModal(); });

function mostrarErrorTicket(mensaje) {
    const errorArea = document.getElementById('formErrorMsg');

    errorArea.textContent = mensaje;
    errorArea.style.display = 'block';
}

function limpiarErrorTicket() {
    const errorArea = document.getElementById('formErrorMsg');

    errorArea.textContent = '';
    errorArea.style.display = 'none';

    document.querySelectorAll('#ticketForm input, #ticketForm textarea').forEach(campo => {
        campo.classList.remove('input-error');
    });
}

function marcarCampoError(idCampo) {
    const campo = document.getElementById(idCampo);

    if (campo) {
        campo.classList.add('input-error');
        campo.focus();
    }
}

function validarDatosTicket(data) {
    const patronNombre = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s.'-]{2,80}$/;
    const patronEmpresa = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9\s.,&()_-]{0,100}$/;
    const patronCorreo = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    const patronTelefono = /^\+?[0-9\s().-]{7,20}$/;
    const patronIPv4 = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;

    if (!data.nombre_solicitante) {
        marcarCampoError('nombre');
        return 'Debe ingresar el nombre del solicitante.';
    }

    if (!patronNombre.test(data.nombre_solicitante)) {
        marcarCampoError('nombre');
        return 'El nombre solo debe contener letras, espacios, puntos, guiones o apóstrofes.';
    }

    if (data.empresa_solicitante && !patronEmpresa.test(data.empresa_solicitante)) {
        marcarCampoError('empresa');
        return 'La empresa o departamento contiene caracteres no permitidos.';
    }

    if (!data.correo_solicitante) {
        marcarCampoError('correo');
        return 'Debe ingresar el correo de contacto.';
    }

    if (!patronCorreo.test(data.correo_solicitante)) {
        marcarCampoError('correo');
        return 'Debe ingresar un correo válido.';
    }

    if (!data.telefono_solicitante) {
        marcarCampoError('telefono');
        return 'Debe ingresar el teléfono de contacto.';
    }

    if (!patronTelefono.test(data.telefono_solicitante)) {
        marcarCampoError('telefono');
        return 'El teléfono solo debe contener números, espacios, paréntesis, guiones o el símbolo +.';
    }

    if (!data.ip_reportada) {
        marcarCampoError('ip');
        return 'Debe ingresar la dirección IP afectada.';
    }

    if (!patronIPv4.test(data.ip_reportada)) {
        marcarCampoError('ip');
        return 'La dirección IP no tiene un formato válido.';
    }

    if (!data.descripcion_problema) {
        marcarCampoError('descripcion');
        return 'Debe ingresar una descripción del problema.';
    }

    if (data.descripcion_problema.length < 5 || data.descripcion_problema.length > 500) {
        marcarCampoError('descripcion');
        return 'La descripción debe tener entre 5 y 500 caracteres.';
    }

    if (/[<>]/.test(data.descripcion_problema)) {
        marcarCampoError('descripcion');
        return 'La descripción contiene caracteres no permitidos.';
    }

    return null;
}

ticketForm.addEventListener('submit', function(e) {
    e.preventDefault();

    limpiarErrorTicket();

    const formData = new FormData(this);

    const data = {
        nombre_solicitante: formData.get('nombre_solicitante').trim(),
        correo_solicitante: formData.get('correo_solicitante').trim().toLowerCase(),
        telefono_solicitante: formData.get('telefono_solicitante').trim(),
        empresa_solicitante: formData.get('empresa_solicitante').trim(),
        ip_reportada: formData.get('ip_reportada').trim(),
        descripcion_problema: formData.get('descripcion_problema').trim()
    };

    const errorValidacion = validarDatosTicket(data);

    if (errorValidacion) {
        mostrarErrorTicket(errorValidacion);
        return;
    }

    const botonEnviar = this.querySelector('.btn-submit');

    botonEnviar.disabled = true;
    botonEnviar.textContent = 'Enviando...';

    fetch('/crear_ticket', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(async response => {
        const respuesta = await response.json().catch(() => ({}));

        if (!response.ok || respuesta.status === 'error') {
            throw new Error(
                respuesta.message ||
                respuesta.mensaje ||
                'No se pudo crear el ticket.'
            );
        }

        return respuesta;
    })
    .then(respuesta => {
        const idDisplay = document.getElementById('ticketIdResult');

        idDisplay.textContent = respuesta.ticket || 'Registrado';

        formView.style.display = 'none';
        successView.style.display = 'block';
    })
    .catch(error => {
        mostrarErrorTicket(error.message);
    })
    .finally(() => {
        botonEnviar.disabled = false;
        botonEnviar.textContent = 'Enviar a Diagnóstico';
    });
});

// =========================================
// Lógica del Modal de Consulta de Tickets
// Versión asegurada: la consulta pública exige código + correo
// y no muestra datos técnicos internos del diagnóstico.
// =========================================
const modalConsultaOverlay = document.getElementById('modalConsultaOverlay');
const btnAbrirModalConsulta = document.getElementById('btnAbrirModalConsulta');
const btnCerrarModalConsultaX = document.getElementById('btnCerrarModalConsultaX');
const btnBuscarTicket = document.getElementById('btnBuscarTicket');
const ticketSearchId = document.getElementById('ticketSearchId');
const ticketSearchCorreo = document.getElementById('ticketSearchCorreo');
const ticketResultArea = document.getElementById('ticketResultArea');
const ticketErrorArea = document.getElementById('ticketErrorArea');

function configEstado(estado) {
    if (estado === "diagnosticado") return { texto: 'Diagnosticado', clase: 'badge-diagnosticado' };
    if (estado === "asignado") return { texto: 'Asignado', clase: 'badge-asignado' };
    if (estado === "cerrado") return { texto: 'Cerrado', clase: 'badge-cerrado' };
    return { texto: 'En Revisión', clase: 'badge-revision' };
}

btnAbrirModalConsulta.addEventListener('click', () => {
    modalConsultaOverlay.classList.add('active');

    ticketSearchId.value = '';
    ticketSearchCorreo.value = '';

    ticketResultArea.style.display = 'none';
    ticketErrorArea.style.display = 'none';
    ticketErrorArea.textContent = '';
});

const cerrarModalConsulta = () => {
    modalConsultaOverlay.classList.remove('active');
};

btnCerrarModalConsultaX.addEventListener('click', cerrarModalConsulta);

modalConsultaOverlay.addEventListener('click', (e) => { 
    if (e.target === modalConsultaOverlay) {
        cerrarModalConsulta();
    }
});

btnBuscarTicket.addEventListener('click', () => {
    const codigoTicket = ticketSearchId.value.trim().toUpperCase();
    const correoSolicitante = ticketSearchCorreo.value.trim().toLowerCase();

    if (!codigoTicket || !correoSolicitante) {
        ticketErrorArea.textContent = "Debe ingresar el código del ticket y el correo del solicitante.";
        ticketErrorArea.style.display = 'block';
        ticketResultArea.style.display = 'none';
        return;
    }

    btnBuscarTicket.textContent = "Consultando...";
    btnBuscarTicket.disabled = true;

    ticketResultArea.style.display = 'none';
    ticketErrorArea.style.display = 'none';
    ticketErrorArea.textContent = '';

    fetch('/consultar_ticket', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            codigo_ticket: codigoTicket,
            correo_solicitante: correoSolicitante
        })
    })
    .then(async response => {
        const data = await response.json().catch(() => ({}));

        if (!response.ok || data.status === "error") {
            throw new Error(
                data.message ||
                data.mensaje ||
                "No se pudo consultar el ticket."
            );
        }

        return data;
    })
    .then(data => {
        const ticket = data.ticket;

        document.getElementById('res-codigo').textContent = ticket.codigo_ticket;

        const estadoConfig = configEstado(ticket.estado);
        const spanEstado = document.getElementById('res-estado');
        spanEstado.className = `badge ${estadoConfig.clase}`;
        spanEstado.textContent = estadoConfig.texto;

        const fechaObj = new Date(ticket.creado_en);
        document.getElementById('res-fecha').textContent =
            isNaN(fechaObj) ? ticket.creado_en : fechaObj.toLocaleString("es-VE");

        document.getElementById('res-empresa').textContent =
            ticket.empresa_solicitante || "No especificada";

        document.getElementById('res-mensaje-estado').textContent =
            ticket.mensaje_estado || "El caso se encuentra registrado en el sistema.";

        ticketResultArea.style.display = 'block';
        lucide.createIcons();
    })
    .catch(error => {
        ticketErrorArea.textContent = error.message;
        ticketErrorArea.style.display = 'block';
    })
    .finally(() => {
        btnBuscarTicket.textContent = "Consultar Estado";
        btnBuscarTicket.disabled = false;
    });
});