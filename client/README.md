# Loyalty Mock — Cliente web

Interfaz HTML que permite interactuar con el [servidor mock de lealtad](../README.md) desde el browser, sin necesidad de Postman o curl.

---

## Cómo usarlo

1. Asegúrate de que el servidor esté corriendo:
   ```bash
   python3 ../loyalty_server.py
   ```
2. Abre `index.html` directamente en el browser:
   ```bash
   open client/index.html
   ```

> No requiere servidor web ni dependencias externas — solo HTML y JS puro.

---

## Configuración

En la cabecera de `index.js` está la única constante que puede necesitar ajuste:

```js
const BASE_URL = "http://localhost:9876";   // URL del servidor mock
```

Cambia `BASE_URL` si el servidor corre en un puerto distinto. El `TARGET_BASE_PATH` y los paths de cada endpoint se obtienen automáticamente del servidor vía `GET /configuration` al arrancar.

---

## Header sticky

Siempre visible en la parte superior. Muestra de un vistazo el estado de la membresía actual:

| Elemento | Descripción |
|---|---|
| Badge de status | Color según estado: verde = `enrolled`, naranja = `notEnrolled`, gris = `unenrolled`, rojo = `declined` |
| Badge de acción | Acción pendiente del servidor (`none`, `displayWelcomeModal`, `displayEnrollModal`) |
| Miembro desde | Fecha de alta en el programa de lealtad |
| Nombre del usuario | `firstName` + `lastName` del estado actual |
| **Actualizar** | Recarga el estado desde `GET /<base>/users/me/loyalty/status` |
| Punto SSE | Círculo verde = push activo · rojo = desconectado (reconectando) |
| **Log** | Abre/cierra el panel de log (izquierdo) |
| **Config** | Abre/cierra el panel de configuración (derecho) |

---

## Panel de log

Se abre y cierra con el botón **Log** del header (resaltado en azul cuando está visible). También se puede cerrar con el backdrop o el botón **✕**.

### Entradas mostradas

El panel muestra todas las operaciones registradas excepto `GET /log` y `GET /configuration` (que son lecturas internas del propio cliente). Las entradas se ordenan de **más reciente a más antigua** (la operación más nueva aparece arriba).

### Formato de cada entrada

```
14:32:05  PATCH  200  [i]
/web-bff/users/me/loyalty/status

ENROLLED / NONE          ← estado resultante
↑ welcomeModalClosed     ← operación
ENROLLED / DISPLAYWELCOMEMODAL   ← estado previo
```

Para operaciones sin transición de estado (p. ej. GET /status) solo se muestra la línea de cabecera y el path.

### Separador entre entradas

Un `↑` separa cada par de entradas consecutivas, indicando que el tiempo fluye hacia arriba.

### Botón de detalle `i`

Abre un modal con todos los campos del log entry y el curl reproducible:

```bash
curl -X PATCH "http://localhost:9876/web-bff/users/me/loyalty/status" \
  -H "Content-Type: application/json" \
  -d '{"action": "welcomeModalClosed", "value": true}'
```

El botón **Copiar** copia el curl al portapapeles.

### Limpiar

El botón **Limpiar** envía `DELETE /log`. El servidor vacía `server.log` y emite el evento SSE `log-cleared`, que limpia la vista del panel inmediatamente.

### Push en tiempo real (SSE)

Al arrancar, el cliente abre una conexión `GET /events` con el servidor. Cada operación que el servidor procesa notifica al cliente vía SSE sin necesidad de polling:

- **`log-entry`** — el cliente prepende la nueva entrada al panel de log. Si el entry incluye `new_status` (cambio de estado) o es un POST enroll exitoso, el cliente también refresca automáticamente los cards de status.
- **`log-cleared`** — el cliente limpia su panel de log.

El punto de color en el header refleja el estado de la conexión SSE: verde = activo, rojo = desconectado (el browser reconecta automáticamente).

---

## Panel de configuración

Se abre y cierra con el botón **⚙️ Config** del header (resaltado en azul cuando está visible). También se puede cerrar con el backdrop o el botón **✕**.

### Secciones del panel

#### Servidor _(solo lectura)_

Muestra la versión del servidor y el puerto activo.

#### Variables _(editables)_

Permite modificar los valores configurables sin reiniciar el servidor:

| Campo | Control | Valores posibles |
|---|---|---|
| Base path del BFF | `<select>` | `pocket-bff` · `web-bff` |
| Cupones de lealtad | `<select>` | `empty` · `full` |
| Cupones canjeados | `<select>` | `empty` · `full` |
| Cupones de checkout | `<select>` | `cart` · `no_cart_error` |
| Loyalty Member ID | texto libre | cualquier string |
| User ID | numérico | cualquier número |

#### Paths activos _(solo lectura)_

Lista los paths que el servidor está atendiendo actualmente, derivados del `TARGET_BASE_PATH` configurado.

### Cambios pendientes

Al modificar cualquier valor del formulario sin haber aplicado los cambios:

- El campo modificado se resalta con **borde azul y fondo celeste**.
- Aparece un aviso amarillo sobre el botón: _"● N cambio(s) pendiente(s) de aplicar"_.
- Al revertir un campo a su valor original, deja de contar como pendiente.

### Aplicar cambios

El botón **Aplicar cambios** envía un `PUT /configuration` con todos los valores del formulario.  
Tras la respuesta exitosa del servidor:

- El panel se repinta con los valores confirmados.
- Los resaltados de cambios pendientes desaparecen.
- El header y los cards se recargan usando el nuevo path de status (útil si cambió el `TARGET_BASE_PATH`).

---

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Estructura y markup: header, cards, panel de log, panel de config, modal |
| `index.css` | Estilos: variables, layout, cards, paneles, log entries, modal |
| `index.js` | Lógica: fetch, render, log panel, SSE, modal de detalle, dirty-state |

---

## Arquitectura del cliente

```
init()
  ├─ GET /configuration → paths + config → renderConfigPanel()
  ├─ GET /<base>/status → renderHeader() + renderLoyaltyCard() + renderUserCard()
  ├─ GET /log           → logEntries[] → renderLogPanel()
  └─ GET /events  (SSE, conexión persistente)
         ├─ "log-entry"   → unshift(entry) → renderLogPanel()
         │                  si new_status → fetchStatus()
         └─ "log-cleared" → logEntries=[] → renderLogPanel()
```

De esta forma, el cliente se mantiene sincronizado con el servidor sin polling: cualquier operación del servidor (desde Postman, curl o la app) actualiza el panel de log y el estado de membresía en tiempo real.
