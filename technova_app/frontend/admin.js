lucide.createIcons();

// Inicializar Calendario
const fp = flatpickr("#filtro-fecha", {
    mode: "range",
    dateFormat: "Y-m-d",
    altInput: true,
    altFormat: "d M Y",
    locale: "es",
    onChange: function(selectedDates, dateStr, instance) {
        interaccionManualTarjeta = false;
        aplicarFiltrosYOrden();
    }
});

// Lógica Dropdowns
const dropdownContainer = document.getElementById('dropdownContainer');
document.getElementById('userBtn').addEventListener('click', (e) => { dropdownContainer.classList.toggle('active'); e.stopPropagation(); });

let interaccionManualTarjeta = false;

document.querySelectorAll('.custom-dropdown').forEach(dropdown => {
    dropdown.addEventListener('click', (e) => {
        if(e.target.closest('.custom-dropdown-list')) return; 
        document.querySelectorAll('.custom-dropdown').forEach(d => { if (d !== dropdown) d.classList.remove('active'); });
        dropdownContainer.classList.remove('active');
        dropdown.classList.toggle('active');
        e.stopPropagation();
    });

    const options = dropdown.querySelectorAll('.custom-option');
    const hiddenInput = dropdown.querySelector('input[type="hidden"]');
    const selectedText = dropdown.querySelector('.selected-text');

    options.forEach(opt => {
        opt.addEventListener('click', (e) => {
            options.forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            selectedText.textContent = opt.textContent;
            hiddenInput.value = opt.getAttribute('data-value');
            dropdown.classList.remove('active');
            interaccionManualTarjeta = false; 
            aplicarFiltrosYOrden();
            e.stopPropagation();
        });
    });
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-dropdown-container')) dropdownContainer.classList.remove('active');
    if (!e.target.closest('.custom-dropdown')) document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('active'));
    
    const dropdownEstado = document.getElementById('estado-dropdown');
    if(dropdownEstado && !e.target.closest('#btn-editar-estado') && !e.target.closest('#estado-dropdown')) {
        dropdownEstado.classList.remove('active');
    }
});

// Limpiar Filtros
document.getElementById('btn-limpiar').addEventListener('click', () => {
    document.getElementById('buscar').value = "";
    document.getElementById('filtro-estado').value = "";
    document.getElementById('text-estado').textContent = "Todos los Estados";
    document.querySelectorAll('#dropdown-estado .custom-option').forEach(o => o.classList.remove('selected'));
    document.querySelector('#dropdown-estado .custom-option[data-value=""]').classList.add('selected');

    document.getElementById('filtro-alerta').value = "";
    document.getElementById('text-alerta').textContent = "Cualquier Alerta";
    document.querySelectorAll('#dropdown-alerta .custom-option').forEach(o => o.classList.remove('selected'));
    document.querySelector('#dropdown-alerta .custom-option[data-value=""]').classList.add('selected');

    fp.clear(); // Limpiar Calendario

    interaccionManualTarjeta = false;
    filtroTarjeta = "total";
    columnaActual = ""; 
    ordenAscendente = true;
    document.querySelectorAll("th[data-sort] .sort-icon").forEach(icon => icon.textContent = "↕");

    aplicarFiltrosYOrden();
});

// Tarjetas Filtros
let filtroTarjeta = "total"; 
document.querySelectorAll('.metric-card').forEach(card => {
    card.addEventListener('click', () => {
        const tipo = card.getAttribute('data-filter');
        interaccionManualTarjeta = true; 
        if (card.classList.contains('active') && tipo !== "total") {
            card.classList.remove('active');
            filtroTarjeta = "total";
            document.querySelector('.metric-card[data-filter="total"]').classList.add('active');
        } else {
            document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            filtroTarjeta = tipo;
        }
        aplicarFiltrosYOrden();
    });
});

document.getElementById("buscar").addEventListener("input", () => { interaccionManualTarjeta = false; aplicarFiltrosYOrden(); });

let ticketsOriginales = [];
let ticketsMostrados = [];
let columnaActual = ""; 
let ordenAscendente = true;
let ticketActualSeleccionado = null; 

// AUTENTICACIÓN Y REDIRECCIÓN 
async function cargarEmpleadoActual() {
    try {
        const respuesta = await fetch("/empleado-actual");
        if (!respuesta.ok) {
            window.location.replace("/login.html"); 
            return;
        }
        const data = await respuesta.json();
        if (data.status !== "ok") {
            window.location.replace("/login.html");
            return;
        }

        document.body.classList.add('visible');

        const empleado = data.empleado;
        document.getElementById("nombre-empleado").textContent = `${empleado.nombre} ${empleado.apellido}`;
        document.getElementById("rol-empleado").textContent = empleado.tipo_empleado.toUpperCase();
        document.getElementById("email-empleado").textContent = empleado.correo;
        document.getElementById("avatar-empleado").textContent = `${empleado.nombre.charAt(0)}${empleado.apellido.charAt(0)}`.toUpperCase();
    } catch (error) {
        window.location.replace("/login.html");
    }
}

// LÓGICA DE CIERRE DE SESIÓN
document.getElementById("btn-cerrar-sesion").addEventListener("click", (e) => {
    e.preventDefault();
    dropdownContainer.classList.remove('active');
    
    const logoutModal = document.getElementById("modal-logout");
    const logoutIcon = document.getElementById("logoutIcon");
    const logoutView = document.getElementById("logoutView");
    
    logoutModal.classList.remove("oculto");
    
    setTimeout(() => {
        logoutIcon.classList.add('done');
        logoutView.classList.add('done');
    }, 100);

    setTimeout(() => {
        window.location.href = '/logout';
    }, 1500);
});

async function cargarTickets() {
    const tabla = document.getElementById("tabla-tickets");
    try {
        const respuesta = await fetch("/tickets");
        const data = await respuesta.json();
        if (data.status !== "ok") { tabla.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--alert); padding: 20px;">Error al cargar datos</td></tr>`; return; }
        ticketsOriginales = data.tickets;
        actualizarResumen(ticketsOriginales);
        aplicarFiltrosYOrden();
    } catch (error) { tabla.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--alert); padding: 20px;">Fallo de comunicación de red</td></tr>`; }
}

function pintarTickets(tickets) {
    const tabla = document.getElementById("tabla-tickets");
    ticketsMostrados = tickets;
    if (tickets.length === 0) { tabla.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 40px; color: #888;">No hay incidentes encontrados.</td></tr>`; return; }

    tabla.innerHTML = "";
    tickets.forEach((ticket, index) => {
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td class="id-text">${limpiar(ticket.codigo_ticket)}</td>
            <td><span class="bold-text">${limpiar(ticket.nombre_solicitante)}</span><span class="sub-text">${limpiar(ticket.empresa_solicitante)}</span></td>
            <td class="id-text" style="color: #444;">${limpiar(ticket.ip_reportada)}</td>
            <td><span class="badge ${claseEstado(ticket.estado)}">${limpiar(ticket.estado).replace('_', ' ').toUpperCase()}</span></td>
            <td><span class="bold-text">${limpiar(ticket.nombre_equipo || "-")}</span><span class="sub-text">${limpiar(ticket.area_equipo || "-")}</span></td>
            <td><span class="diag-badge">${limpiar(ticket.codigo_diagnostico)}</span></td>
            <td><span class="${claseAlerta(ticket.nivel_alerta)}">${limpiar(ticket.nivel_alerta || "-").toUpperCase()}</span></td>
            <td style="font-size: 12px; color: #666;">${formatearFecha(ticket.creado_en)}</td>
            <td><button class="btn-action btn-ver" data-index="${index}"><i data-lucide="eye" style="width: 14px;"></i> Analizar</button></td>
        `;
        tabla.appendChild(fila);
    });
    lucide.createIcons(); 
}

function actualizarResumen(tickets) {
    document.getElementById("total-tickets").textContent = tickets.length;
    document.getElementById("total-diagnosticados").textContent = tickets.filter(t => t.estado === "diagnosticado").length;
    document.getElementById("total-revision").textContent = tickets.filter(t => t.estado === "en_revision").length;
    document.getElementById("total-altas").textContent = tickets.filter(t => t.nivel_alerta === "alta" || t.nivel_alerta === "critica").length;
}

document.querySelectorAll("th[data-sort]").forEach(th => {
    th.addEventListener("click", () => {
        const columna = th.getAttribute("data-sort");
        if (columnaActual === columna) ordenAscendente = !ordenAscendente; 
        else { columnaActual = columna; ordenAscendente = true; }
        document.querySelectorAll("th[data-sort] .sort-icon").forEach(icon => icon.textContent = "↕");
        th.querySelector(".sort-icon").textContent = ordenAscendente ? "↑" : "↓";
        aplicarFiltrosYOrden();
    });
});

function aplicarFiltrosYOrden() {
    const texto = document.getElementById("buscar").value.toLowerCase();
    const estado = document.getElementById("filtro-estado").value;
    const alerta = document.getElementById("filtro-alerta").value;
    const fechasSeleccionadas = fp.selectedDates;
    const cardTotal = document.querySelector('.metric-card[data-filter="total"]');
    
    if (!interaccionManualTarjeta) {
        if (texto === "" && estado === "" && alerta === "" && fechasSeleccionadas.length === 0 && filtroTarjeta === "total") {
            document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active'));
            cardTotal.classList.add('active'); 
        } else { cardTotal.classList.remove('active'); }
    }

    let filtrados = ticketsOriginales.filter(ticket => {
        const coincideTexto = String(ticket.codigo_ticket || "").toLowerCase().includes(texto) || String(ticket.ip_reportada || "").toLowerCase().includes(texto) || String(ticket.empresa_solicitante || "").toLowerCase().includes(texto) || String(ticket.nombre_solicitante || "").toLowerCase().includes(texto);
        const coincideEstado = estado === "" || ticket.estado === estado;
        const coincideAlerta = alerta === "" || ticket.nivel_alerta === alerta; 
        const coincideTarjeta = filtroTarjeta === "total" || (filtroTarjeta === "diagnosticado" && ticket.estado === "diagnosticado") || (filtroTarjeta === "revision" && ticket.estado === "en_revision") || (filtroTarjeta === "critica" && (ticket.nivel_alerta === "alta" || ticket.nivel_alerta === "critica"));
        
        let coincideFecha = true;
        if (fechasSeleccionadas.length > 0 && ticket.creado_en) {
            const ticketDate = new Date(ticket.creado_en);
            ticketDate.setHours(0,0,0,0);
            
            const startDate = new Date(fechasSeleccionadas[0]);
            startDate.setHours(0,0,0,0);

            if (fechasSeleccionadas.length === 1) {
                coincideFecha = ticketDate.getTime() === startDate.getTime();
            } else if (fechasSeleccionadas.length === 2) {
                const endDate = new Date(fechasSeleccionadas[1]);
                endDate.setHours(0,0,0,0);
                coincideFecha = ticketDate >= startDate && ticketDate <= endDate;
            }
        }

        return coincideTexto && coincideEstado && coincideAlerta && coincideTarjeta && coincideFecha;
    });

    if (columnaActual) {
        filtrados.sort((a, b) => {
            let vA = a[columnaActual] || ""; let vB = b[columnaActual] || "";
            if (columnaActual === 'creado_en') { vA = new Date(vA).getTime() || 0; vB = new Date(vB).getTime() || 0; } 
            else { vA = String(vA).toLowerCase(); vB = String(vB).toLowerCase(); }
            if (vA < vB) return ordenAscendente ? -1 : 1;
            if (vA > vB) return ordenAscendente ? 1 : -1;
            return 0;
        });
    }
    pintarTickets(filtrados);
}

// ABRIR MODAL PRINCIPAL
document.getElementById("tabla-tickets").addEventListener("click", function(e) {
    const boton = e.target.closest('.btn-ver');
    if (boton) {
        const index = boton.getAttribute("data-index");
        ticketActualSeleccionado = ticketsMostrados[index].codigo_ticket;
        abrirModalTicket(ticketsMostrados[index]);
    }
});

function abrirModalTicket(ticket) {
    if(!ticket) return;
    document.getElementById("modal-codigo").textContent = ticket.codigo_ticket;
    const headerEstado = document.getElementById("modal-estado-header");
    headerEstado.className = `badge ${claseEstado(ticket.estado)}`;
    headerEstado.textContent = ticket.estado.replace('_', ' ').toUpperCase();
    
    document.getElementById("modal-solicitante").textContent = ticket.nombre_solicitante || "-";
    document.getElementById("modal-contacto").textContent = `${ticket.correo_solicitante || "-"} | ${ticket.telefono_solicitante || "-"}`;
    document.getElementById("modal-empresa").textContent = ticket.empresa_solicitante || "-";
    document.getElementById("modal-ip").textContent = ticket.ip_reportada || "-";
    document.getElementById("modal-creado").textContent = formatearFecha(ticket.creado_en);
    document.getElementById("modal-descripcion").textContent = ticket.descripcion_problema || "Sin descripción.";
    document.getElementById("modal-equipo").textContent = ticket.nombre_equipo || "Desconocido";
    document.getElementById("modal-area").textContent = ticket.area_equipo || "-";
    document.getElementById("modal-estado-equipo").textContent = ticket.estado_equipo || "-";
    document.getElementById("modal-latencia").textContent = ticket.latencia_ms ? `${ticket.latencia_ms} ms` : "N/A";
    document.getElementById("modal-codigo-diagnostico").textContent = ticket.codigo_diagnostico || "-";
    document.getElementById("modal-alerta").textContent = ticket.nivel_alerta ? ticket.nivel_alerta.toUpperCase() : "-";
    document.getElementById("modal-mensaje").textContent = ticket.mensaje_diagnostico || "Sin logs registrados.";
    document.getElementById("modal-recomendacion").textContent = ticket.recomendacion || "Análisis manual requerido.";

    document.getElementById("modal-ticket").classList.remove("oculto");
}

// LÓGICA DE CAMBIO DE ESTADO
document.getElementById('btn-editar-estado').addEventListener('click', (e) => {
    document.getElementById('estado-dropdown').classList.toggle('active');
    e.stopPropagation();
});

document.querySelectorAll('.estado-option').forEach(opcion => {
    opcion.addEventListener('click', async () => {
        const nuevoEstado = opcion.getAttribute('data-estado');
        document.getElementById('estado-dropdown').classList.remove('active');
        
        const headerEstado = document.getElementById("modal-estado-header");
        headerEstado.className = `badge ${claseEstado(nuevoEstado)}`;
        headerEstado.textContent = nuevoEstado.replace('_', ' ').toUpperCase();

        await fetch('/cambiar_estado', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticket_id: ticketActualSeleccionado, nuevo_estado: nuevoEstado })
        });

        cargarTickets(); 
    });
});

// LÓGICA DE MODAL DE CORREO
document.getElementById("btn-abrir-correo").addEventListener("click", () => {
    document.getElementById("email-asunto").value = `Escalamiento de Incidente ${ticketActualSeleccionado}`;
    document.getElementById("modal-email").classList.remove("oculto");
});

document.getElementById("btn-cerrar-email").addEventListener("click", () => document.getElementById("modal-email").classList.add("oculto"));
document.getElementById("btn-cancelar-email").addEventListener("click", () => document.getElementById("modal-email").classList.add("oculto"));

document.getElementById("btn-enviar-email").addEventListener("click", async () => {
    const analista = document.getElementById("email-para").value;
    const mensaje = document.getElementById("email-mensaje").value;

    await fetch('/asignar_ticket', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_id: ticketActualSeleccionado, analista: analista, mensaje: mensaje })
    });

    document.getElementById("modal-email").classList.add("oculto");
    document.getElementById("modal-ticket").classList.add("oculto");
    
    const successModal = document.getElementById("modal-success-email");
    const successIcon = document.getElementById("emailSuccessIcon");
    const successView = document.getElementById("emailSuccessView");
    
    successIcon.classList.remove('done');
    successView.classList.remove('done');
    
    successModal.classList.remove("oculto");
    
    setTimeout(() => {
        successIcon.classList.add('done');
        successView.classList.add('done');
    }, 800);

    cargarTickets(); 
    
    document.getElementById("email-para").value = "";
    document.getElementById("email-mensaje").value = "";
});

document.getElementById("btn-cerrar-success").addEventListener("click", () => {
    document.getElementById("modal-success-email").classList.add("oculto");
});

function claseEstado(estado) {
    if (estado === "diagnosticado") return "badge-diagnosticado";
    if (estado === "en_revision") return "badge-revision";
    if (estado === "cerrado") return "badge-cerrado";
    if (estado === "asignado") return "badge-asignado";
    return "badge-abierto";
}
function claseAlerta(alerta) {
    if (alerta === "baja") return "alerta-baja";
    if (alerta === "media") return "alerta-media";
    if (alerta === "alta") return "alerta-alta";
    if (alerta === "critica") return "alerta-critica";
    return "";
}
function formatearFecha(fecha) {
    if (!fecha) return "-";
    const date = new Date(fecha);
    return isNaN(date.getTime()) ? fecha : date.toLocaleString("es-VE");
}
function limpiar(valor) {
    if (valor == null) return "";
    return String(valor).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

document.querySelector(".btn-close-main").addEventListener("click", () => document.getElementById("modal-ticket").classList.add("oculto"));

cargarEmpleadoActual();
cargarTickets();