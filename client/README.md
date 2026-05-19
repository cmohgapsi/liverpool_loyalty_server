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

## Layout

El cliente usa un layout de **tres columnas** que comparten el espacio horizontal:

```
┌─────────────────────────────────────────────────────────┐
│                       Header sticky                      │
├──────────────┬──────────────────────────┬───────────────┤
│  Log panel   │         Main             │ Config panel  │
│  (380 px)    │   (flex: 1, scroll)      │  (360 px)     │
│  ocultable   │                          │  ocultable    │
└──────────────┴──────────────────────────┴───────────────┘
```

Ambos paneles laterales se muestran/ocultan con los botones del header y **nunca se superponen** al contenido central — empujan el `main` al abrirse.

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

Se abre y cierra con el botón **Log** del header (resaltado en azul cuando está visible). También se puede cerrar con el botón **✕**.

### Entradas mostradas

El panel muestra todas las operaciones registradas excepto `GET /log`, `GET /configuration` y `GET /events` (lecturas internas del propio cliente). Las entradas se ordenan de **más reciente a más antigua**.

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

Abre un modal con todos los campos del log entry, el curl reproducible y el response del servidor (ambos en bloques de código con botón **Copiar**):

```bash
curl -X PATCH "http://localhost:9876/web-bff/users/me/loyalty/status" \
  -H "Content-Type: application/json" \
  -d '{"action": "welcomeModalClosed", "value": true}'
```

### Limpiar

El botón **Limpiar** envía `DELETE /log`. El servidor vacía `server.log` y emite el evento SSE `log-cleared`, que limpia la vista del panel inmediatamente.

### Push en tiempo real (SSE)

Al arrancar, el cliente abre una conexión `GET /events` con el servidor. Cada operación que el servidor procesa notifica al cliente vía SSE sin polling:

- **`log-entry`** — el cliente prepende la nueva entrada al panel de log. Si el entry incluye `new_status` o es un POST enroll exitoso, también refresca el header y el card de usuario.
- **`log-cleared`** — el cliente limpia su panel de log.

El punto de color en el header refleja el estado de la conexión SSE: verde = activo, rojo = desconectado (el browser reconecta automáticamente).

---

## Panel de configuración

Se abre y cierra con el botón **Config** del header (resaltado en azul cuando está visible). También se puede cerrar con el botón **✕**.

### Secciones del panel

#### Servidor _(solo lectura)_

Muestra la versión del servidor y el puerto activo.

#### Variables _(editables)_

Permite modificar los valores configurables sin reiniciar el servidor:

| Campo | Control | Valores posibles |
|---|---|---|
| Base path del BFF | `<select>` | `pocket-bff` · `web-bff` |
| Cupones de lealtad | `<select>` | `empty` · `full` · `server_error` · `bad_request` |
| Cupones canjeados | `<select>` | `empty` · `full` |
| Cupones de checkout | `<select>` | `cart` · `no_cart_error` |
| Loyalty Member ID | texto libre | cualquier string |
| User ID | numérico | cualquier número |

#### Paths activos _(solo lectura)_

Lista los paths que el servidor está atendiendo actualmente, derivados del `TARGET_BASE_PATH` configurado.

### Cambios pendientes

Al modificar cualquier valor sin haber aplicado los cambios:

- El campo modificado se resalta con **borde azul y fondo celeste**.
- Aparece un aviso amarillo: _"● N cambio(s) pendiente(s) de aplicar"_.
- Al revertir un campo a su valor original, deja de contar como pendiente.

### Aplicar cambios

El botón **Aplicar cambios** envía un `PUT /configuration`. Tras la respuesta exitosa:

- El panel se repinta con los valores confirmados.
- Los resaltados de cambios pendientes desaparecen.
- El header y el card de usuario se recargan con el nuevo path de status.

---

## Sección de Operaciones

Selector de radio buttons estilo pill (uno por operación). Al seleccionar una, se muestra el card correspondiente; las demás se ocultan. Por defecto ninguna está seleccionada.

### Set Status

Envía `PATCH /<base>/users/me/loyalty/status` con la acción seleccionada y `value: true`.

| Acción | Transición |
|---|---|
| `welcomeModalClosed` | enrolled / displayWelcomeModal → enrolled / none |
| `enrollModalClosed` | → declined / none |
| `displayWelcomeModal` | → enrolled / displayWelcomeModal |
| `displayEnrollModal` | → notEnrolled / displayEnrollModal |

### Cancel Enroll

Envía `PATCH /<base>/users/me/loyalty/status` con `action: "unenroll"` y el `cancelReason` seleccionado.

- Las razones se cargan automáticamente desde `GET /<base>/loyalty/cancel-reasons` al iniciar (esta llamada **no se registra en el log** gracias al header `server-log: false`).
- Al seleccionar **"Otro…"** aparece un campo de texto para introducir una razón personalizada.
- El servidor retorna **409** si el estado actual no es `enrolled`.

### Enroll

Envía `POST /<base>/users/me/loyalty/enroll` con los datos del formulario. Todos los campos son obligatorios:

| Campo | Descripción |
|---|---|
| Nombre | `firstName` |
| Apellido paterno | `lastName` |
| Apellido materno | `motherLastName` |
| Género | `M` · `F` · `I` |
| Fecha de nacimiento | `dateOfBirth` (DD/MM/AAAA) |

### ReEnroll

Envía `POST /<base>/users/me/loyalty/enroll` con body vacío `{}`. Disponible cuando el estado es `unenrolled`.

### Coupons

Tres operaciones de consulta (GET), cada una con su botón:

| Botón | Endpoint | Parámetro |
|---|---|---|
| **Loyalty Coupons** | `GET /<base>/users/me/loyalty/coupons` | — |
| **Redeemed Coupons** | `GET /<base>/users/me/loyalty/coupons/redeemed` | — |
| **Checkout Coupons** | `GET /<base>/checkout/coupons` | `isBuyNow` (true · false) |

El selector `isBuyNow` y el botón de Checkout Coupons se presentan en una subsección visualmente separada para dejar claro que el parámetro pertenece a esa operación.

---

## Comportamiento del log en el cliente

Las siguientes llamadas se realizan con el header `server-log: false` y **no aparecen en el panel de log**:

- `GET /<base>/users/me/loyalty/status` (refresco automático de estado)
- `GET /<base>/loyalty/cancel-reasons` (carga de razones de cancelación)

Todas las operaciones de la sección **Operaciones** sí se registran.

---

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Estructura y markup: header, panel de log, main, panel de config, modal |
| `index.css` | Estilos: variables, layout 3 columnas, paneles, radio group, log entries, modal |
| `index.js` | Lógica: fetch, render, SSE, operaciones, modal de detalle, dirty-state |

---

## Arquitectura del cliente

```
init()
  ├─ GET /configuration → paths + config → renderConfigPanel()
  ├─ GET /<base>/status → renderHeader() + renderUserCard()   [server-log: false]
  ├─ GET /log           → logEntries[] → renderLogPanel()
  ├─ GET /<base>/cancel-reasons → poblar select              [server-log: false]
  ├─ GET /events  (SSE, conexión persistente)
  │      ├─ "log-entry"   → unshift(entry) → renderLogPanel()
  │      │                  si new_status o POST 200 → fetchStatus()
  │      └─ "log-cleared" → logEntries=[] → renderLogPanel()
  └─ attach radio listeners → mostrar/ocultar ops-card por valor
```
