# Proxyman — Mock de flujo de Lealtad

Simula las transiciones de estado del sistema de lealtad interceptando un `PATCH` y modificando la respuesta del `GET` subsecuente, sin tocar ninguna regla de Proxyman en tiempo de ejecución.

---

## Estructura de archivos

```
proxyman-loyalty/
├── states/
│   ├── current_state.json              ← Map Local apunta aquí (GET)
│   ├── enrolled_welcome_state.json
│   ├── enrolled_none_state.json
│   ├── notEnrolled_enroll_state.json
│   ├── declined_none_state.json
│   └── unenrolled_none_state.json
├── responses/
│   ├── path_status_enroll_welcome.json
│   ├── path_status_notEnrolled_enroll.json
│   ├── path_status_enrolled.json
│   ├── path_status_declined.json
│   └── path_status_unenroll.json
├── loyalty_server.py                     ← Servidor local (único archivo necesario)
└── README.md
```

---

## Requisitos

- macOS con **Proxyman** instalado
- **Python 3** (incluido en macOS por defecto)
- La carpeta copiada en tu máquina (ajusta `BASE_PATH` en `loyalty_server.py` si la mueves)

---

## Setup en Proxyman

### 1. Map Local — GET de usuario

| Campo | Valor |
|---|---|
| URL | `https://ogcp-apigke-qa1.liverpool.com.mx/pocket-bff/users/me` |
| Método | `GET` |
| Local file | `…/states/current_state.json` |
| Opción | ✅ **Use file content as raw HTTP response** |

### 2. Map Remote — PATCH de estado de lealtad

Redirige el PATCH directamente al servidor local. No se necesita ningún Script.

| Campo | Valor |
|---|---|
| Match URL | `https://ogcp-apigke-qa1.liverpool.com.mx/pocket-bff/users/me/loyalty/status` |
| Método | `PATCH` |
| Redirect to | `http://localhost:9876/loyalty/status` |

---

## Cómo ejecutar la prueba

### Paso 1 — Iniciar el servidor

Abre una terminal y deja corriendo:

```bash
python3 /ruta/a/decommission/loyalty_server.py
```

Deberías ver:

```
🚀  Loyalty server corriendo en http://localhost:9876
📁  States:    …/states
📁  Responses: …/responses
```

> Mantén esta terminal abierta durante toda la sesión de prueba.

### Paso 2 — Verificar el estado inicial

`current_state.json` arranca con `notEnrolled + displayEnrollModal`. El `GET` desde la app debería mostrar el modal de enrolamiento.

### Paso 3 — Disparar los escenarios

Ejecuta el `PATCH` desde la app con los siguientes bodies:

---

**Escenario 1 · Enrolamiento iniciado** → muestra welcome modal
```json
{ "action": "displayWelcomeModal", "value": true }
```
Estado siguiente: `enrolled_welcome` · Respuesta: `path_status_enroll_welcome.json`

---

**Escenario 2 · Modal de enrolamiento** → muestra enroll modal
```json
{ "action": "displayEnrollModal", "value": true }
```
Estado siguiente: `notEnrolled_enroll` · Respuesta: `path_status_notEnrolled_enroll.json`

---

**Escenario 3 · Cuenta creada** → cierra welcome modal
```json
{ "action": "welcomeModalClosed", "value": true }
```
Estado siguiente: `enrolled_none` · Respuesta: `path_status_enrolled.json`

---

**Escenario 4 · Enrolamiento declinado** → cierra enroll modal
```json
{ "action": "enrollModalClosed", "value": true }
```
Estado siguiente: `declined_none` · Respuesta: `path_status_declined.json`

---

**Escenario 5 · Desenrolamiento**
```json
{ "action": "unenroll", "value": true }
```
Estado siguiente: `unenrolled_none` · Respuesta: `path_status_unenroll.json`

---

### Paso 4 — Verificar la transición

Después de cada `PATCH`, el `GET` ya devolverá el nuevo estado. En la terminal del servidor verás la transición confirmada:

```
📨  PATCH recibido → action='welcomeModalClosed', value=True
✅  enrolled_none_state.json  →  current_state.json
📤  Retornando path_status_enrolled.json
```

---

## Reiniciar el estado manualmente

```bash
# Volver a notEnrolled (estado inicial)
cp states/notEnrolled_enroll_state.json states/current_state.json

# Cualquier otro estado
cp states/enrolled_welcome_state.json states/current_state.json
```

---

## Mapa de escenarios

| `action` | `value` | Estado siguiente | Respuesta |
|---|---|---|---|
| `displayWelcomeModal` | `true` | `enrolled_welcome_state` | `path_status_enroll_welcome` |
| `displayEnrollModal` | `true` | `notEnrolled_enroll_state` | `path_status_notEnrolled_enroll` |
| `welcomeModalClosed` | `true` | `enrolled_none_state` | `path_status_enrolled` |
| `enrollModalClosed` | `true` | `declined_none_state` | `path_status_declined` |
| `unenroll` | `true` | `unenrolled_none_state` | `path_status_unenroll` |

---

## Cómo funciona

```
App → PATCH /loyalty/status
        │
        ▼
  Proxyman Map Remote
  redirige a localhost:9876
        │
        ▼
  loyalty_server.py
        ├─ Lee action + value del body
        ├─ Busca en SCENARIOS
        ├─ Copia state_X.json → current_state.json
        └─ Lee y parsea responses/path_status_X.json
        │
        ▼
App ← response del PATCH

App → GET /users/me
        │
        ▼
  Proxyman Map Local
  lee current_state.json  ← ya fue actualizado
        │
        ▼
App ← nuevo estado
```
