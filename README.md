# Proxyman — Mock de flujo de Lealtad

Servidor local que intercepta llamadas redirigidas por Proxyman (Map Remote) para simular las transiciones de estado del sistema de lealtad, sin tocar ninguna regla de Proxyman en tiempo de ejecución.

Atiende doce endpoints. El prefijo `<base>` corresponde al valor de `TARGET_BASE_PATH` en `.env` (`pocket-bff` o `web-bff`):

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/configuration` | Devuelve la configuración activa del servidor |
| `PUT` | `/configuration` | Actualiza en memoria los valores de configuración |
| `GET` | `/log` | Devuelve el historial de requests (más reciente primero) |
| `DELETE` | `/log` | Vacía el historial de requests (`server.log`) |
| `GET` | `/events` | Stream SSE — notifica al cliente tras cada operación |
| `GET` | `/<base>/users/me/loyalty/status` | Devuelve `current_state.json` |
| `GET` | `/<base>/users/me/loyalty/coupons` | Devuelve lista de cupones según `COUPONS_LIST_SUFFIX` |
| `GET` | `/<base>/users/me/loyalty/coupons/redeemed` | Devuelve cupones canjeados según `COUPONS_REDEEMED_SUFFIX` |
| `GET` | `/<base>/checkout/coupons?isBuyNow=<bool>` | Devuelve cupones de checkout según `CHECKOUT_COUPONS_SUFFIX` |
| `GET` | `/<base>/loyalty/cancel-reasons` | Devuelve `get_loyalty_cancel_reasons.json` |
| `POST` | `/<base>/users/me/loyalty/enroll` | Enrola o re-enrola al usuario según su estado actual |
| `PATCH` | `/<base>/users/me/loyalty/status` | Aplica transición de estado y devuelve el response correspondiente |

---

## Estructura de archivos

```
decommission/
├── client/
│   ├── index.html                          ← Cliente web (abrir en browser con el servidor corriendo)
│   ├── index.css                           ← Estilos del cliente
│   ├── index.js                            ← Lógica del cliente
│   └── README.md                           ← Documentación del cliente → ver client/README.md
├── documentation/
│   ├── LIVERPOOL-DECOMMISSION.postman_collection.json        ← Colección Postman con los endpoints
│   ├── LIVERPOOL-DECOMMISSION.postman_environment.json       ← Entorno Postman (pocket-bff)
│   ├── LIVERPOOL-DECOMMISSION WEB.postman_environment.json   ← Entorno Postman (web-bff)
│   └── LoyaltyStatus.png                                     ← Diagrama de estados de lealtad
├── states/
│   ├── current_state.json              ← Estado actual (leído y modificado por varios endpoints)
│   ├── enrolled_welcome_state.json
│   ├── enrolled_none_state.json
│   ├── notEnrolled_enroll_state.json
│   ├── declined_none_state.json
│   └── unenrolled_none_state.json
├── responses/
│   ├── path_status_enrolled.json                         ← PATCH welcomeModalClosed → enrolled/none
│   ├── path_status_enroll_welcome.json                   ← PATCH displayWelcomeModal → enrolled/displayWelcomeModal
│   ├── path_status_notEnrolled_enroll.json               ← PATCH displayEnrollModal → notEnrolled/displayEnrollModal
│   ├── path_status_declined.json                         ← PATCH enrollModalClosed → declined/none
│   ├── path_status_unenroll.json                         ← PATCH unenroll → unenrolled/none
│   ├── get_loyalty_coupons_enrolled_empty.json           ← COUPONS_LIST_SUFFIX=empty
│   ├── get_loyalty_coupons_enrolled_full.json            ← COUPONS_LIST_SUFFIX=full
│   ├── get_loyalty_coupons_enrolled_server_error.json    ← COUPONS_LIST_SUFFIX=server_error
│   ├── get_loyalty_coupons_enrolled_bad_request.json     ← COUPONS_LIST_SUFFIX=bad_request
│   ├── get_loyalty_coupons_enrolled_200_status_error.json← COUPONS_LIST_SUFFIX=200_status_error
│   ├── get_loyalty_coupons_redeemed_empty.json           ← COUPONS_REDEEMED_SUFFIX=empty
│   ├── get_loyalty_coupons_redeemed_full.json            ← COUPONS_REDEEMED_SUFFIX=full
│   ├── get_checkout_coupons_cart.json                    ← CHECKOUT_COUPONS_SUFFIX=cart
│   ├── get_checkout_coupons_no_cart_error.json           ← CHECKOUT_COUPONS_SUFFIX=no_cart_error
│   ├── get_loyalty_cancel_reasons.json                   ← GET cancel-reasons (fallback)
│   └── web-bff/
│       └── get_checkout_coupons_cart.json                ← override para web-bff
├── .env                                ← Variables de entorno (no versionado, créalo desde .env-example)
├── .env-example                        ← Plantilla de variables de entorno
├── loyalty_server.py                   ← Servidor local: routing, ThreadingHTTPServer, entry point
├── config_handler.py                   ← CONFIG, _paths(), GET/PUT /configuration (ConfigHandlerMixin)
├── log_handler.py                      ← GET/DELETE /log (LogHandlerMixin)
├── events_handler.py                   ← GET /events SSE + push_log_entry() (EventsHandlerMixin)
├── coupons_handler.py                  ← Handler y lógica de cupones (CouponsHandlerMixin)
├── enroll_handler.py                   ← Handler y lógica de enrolamiento (EnrollHandlerMixin)
├── status_handler.py                   ← Handler y lógica de status (StatusHandlerMixin, SCENARIOS)
├── state_utils.py                      ← Utilidades compartidas (load_env, extract_json_body, log_request, resolve_response_file, …)
├── server.log                          ← Historial de requests (generado automáticamente, ignorado en git)
└── README.md
```

---

## Requisitos

- macOS con **Proxyman** instalado
- **Python 3** (incluido en macOS por defecto)
- Sin dependencias externas — solo librería estándar

---

## Configuración

### `.env`

Copia `.env-example` y ajusta `BASE_PATH` a tu máquina:

```bash
cp .env-example .env
```

```env
VERSION=1.0.0
BASE_PATH=/ruta/absoluta/a/decommission
PORT=9876
TARGET_BASE_PATH=pocket-bff
COUPONS_LIST_SUFFIX=empty
COUPONS_REDEEMED_SUFFIX=empty
LOYALTY_MEMBER_ID=720100015844
USER_ID=2465729859
CHECKOUT_COUPONS_SUFFIX=cart
```

| Variable | Valores | Descripción |
|---|---|---|
| `VERSION` | string | Versión del servidor, visible en el startup log y en `/configuration`. |
| `BASE_PATH` | ruta absoluta | Ruta a la carpeta `decommission/`. Ajústala si mueves el proyecto. |
| `PORT` | `9876` | Puerto del servidor local. |
| `TARGET_BASE_PATH` | `pocket-bff` · `web-bff` | Prefijo base de todos los endpoints. Cambia este valor para apuntar a un BFF distinto. |
| `COUPONS_LIST_SUFFIX` | `empty` · `full` · `server_error` · `bad_request` · `200_status_error` | Archivo de cupones de lealtad a servir. |
| `COUPONS_REDEEMED_SUFFIX` | `empty` · `full` | Archivo de cupones canjeados a servir. |
| `LOYALTY_MEMBER_ID` | string | ID de miembro de lealtad retornado en el response de enroll. |
| `USER_ID` | número | ID de usuario retornado en el response de enroll. |
| `CHECKOUT_COUPONS_SUFFIX` | `cart` · `no_cart_error` | Archivo de cupones de checkout a servir. |
| `DELAY_MS` | número ≥ 0 | Milisegundos de delay antes de responder. `0` = sin delay. No aplica para `/log` ni `/configuration`. No aplica si el request lleva `server_delay: false`. |

---

## Setup en Proxyman

Configura una sola regla Map Remote que cubra todos los endpoints según el `TARGET_BASE_PATH` configurado.

**Use Regex**

**RULE** (regex — reemplaza `<base>` con el valor de `TARGET_BASE_PATH`):
```
https?://[^/]+(/<base>/(?:users/me/loyalty/.*|checkout/coupons|loyalty/cancel-reasons))
```

Ejemplo con `TARGET_BASE_PATH=pocket-bff`:
```
https?://[^/]+(/pocket-bff/(?:users/me/loyalty/.*|checkout/coupons|loyalty/cancel-reasons))
```

**Método:** `ANY`
**Protocol:** `http`
**Port:** `9876`
**Path (deja el path en blanco):** ``

> Si cambias `TARGET_BASE_PATH` (en `.env` o vía `PUT /configuration`), actualiza también la regla de Proxyman con el nuevo valor.

---

## Cómo ejecutar

```bash
python3 /ruta/a/decommission/loyalty_server.py
```

Salida esperada (con `TARGET_BASE_PATH=pocket-bff`):

```
🚀  Loyalty server corriendo en http://localhost:9876  [v1.0.0]
🗂️   Base path:  /pocket-bff
📁  States:    …/states
📁  Responses: …/responses
🌐  GET    /configuration
🌐  GET    /log
🌐  GET    /events  (SSE — push de eventos)
🌐  PUT    /configuration
🌐  DELETE /log
🌐  GET   /pocket-bff/users/me/loyalty/status
🌐  GET   /pocket-bff/users/me/loyalty/coupons  [suffix=full]
🌐  GET   /pocket-bff/users/me/loyalty/coupons/redeemed  [suffix=empty]
🌐  GET   /pocket-bff/checkout/coupons?isBuyNow=<bool>  [suffix=cart]
🌐  GET   /pocket-bff/loyalty/cancel-reasons
🌐  POST  /pocket-bff/users/me/loyalty/enroll
🌐  PATCH /pocket-bff/users/me/loyalty/status
```

> Mantén esta terminal abierta durante toda la sesión de prueba.

---

## Override de respuestas por subcarpeta

Antes de servir cualquier archivo de `responses/`, el servidor busca primero en `responses/<base>/` (donde `<base>` es el primer segmento del path de la petición, equivalente a `TARGET_BASE_PATH`).

Si el archivo existe ahí, lo sirve en lugar del archivo por defecto:

```
responses/
├── get_loyalty_cancel_reasons.json          ← fallback por defecto
└── pocket-bff/
    └── get_loyalty_cancel_reasons.json      ← override: se sirve este si existe
```

Esto permite mantener variantes por entorno sin modificar los archivos base.

---

## Endpoints

### GET `/configuration`

Devuelve la configuración activa. Los valores reflejan el estado en memoria (inicialmente los del `.env`, modificables en caliente con `PUT /configuration`). No requiere base path ni parámetros.

```json
{
  "version": "1.0.0",
  "PORT": 9876,
  "TARGET_BASE_PATH": "pocket-bff",
  "COUPONS_LIST_SUFFIX": "full",
  "COUPONS_REDEEMED_SUFFIX": "full",
  "CHECKOUT_COUPONS_SUFFIX": "cart",
  "LOYALTY_MEMBER_ID": "720100015844",
  "USER_ID": 2465729859,
  "DELAY_MS": 0,
  "paths": {
    "status":          "/pocket-bff/users/me/loyalty/status",
    "coupons":         "/pocket-bff/users/me/loyalty/coupons",
    "redeemed":        "/pocket-bff/users/me/loyalty/coupons/redeemed",
    "enroll":          "/pocket-bff/users/me/loyalty/enroll",
    "checkoutCoupons": "/pocket-bff/checkout/coupons",
    "cancelReasons":   "/pocket-bff/loyalty/cancel-reasons",
    "configuration":   "/configuration"
  }
}
```

```
📨  GET /configuration
📤  Retornando configuración del servidor
```

---

### PUT `/configuration`

Actualiza en memoria uno o más valores configurables sin reiniciar el servidor. Los campos no reconocidos se ignoran.

**Campos configurables:**

| Campo | Tipo | Valores posibles |
|---|---|---|
| `TARGET_BASE_PATH` | string | `pocket-bff` · `web-bff` |
| `COUPONS_LIST_SUFFIX` | string | `empty` · `full` · `server_error` · `bad_request` · `200_status_error` |
| `COUPONS_REDEEMED_SUFFIX` | string | `empty` · `full` |
| `CHECKOUT_COUPONS_SUFFIX` | string | `cart` · `no_cart_error` |
| `LOYALTY_MEMBER_ID` | string | cualquier string |
| `USER_ID` | number | cualquier número |
| `DELAY_MS` | number | milisegundos de delay (0 = sin delay) |

**Body de ejemplo:**
```json
{ "TARGET_BASE_PATH": "web-bff", "COUPONS_LIST_SUFFIX": "full" }
```

**Response 200:**
```json
{
  "status": { "status": "OK", "statusCode": 0 },
  "updated": { "TARGET_BASE_PATH": "web-bff", "COUPONS_LIST_SUFFIX": "full" },
  "configuration": { "version": "1.0.0", "TARGET_BASE_PATH": "web-bff", "…": "…", "paths": {} }
}
```

```
🔧  PUT /configuration
    TARGET_BASE_PATH = web-bff
    COUPONS_LIST_SUFFIX = full
```

> Si cambias `TARGET_BASE_PATH`, actualiza también la regla de Map Remote en Proxyman.

---

### GET `/log`

Devuelve un arreglo JSON con todos los requests registrados en `server.log`, ordenados del más reciente al más antiguo.

**Response 200:**
```json
[
  {
    "method": "PATCH",
    "path": "/web-bff/users/me/loyalty/status",
    "http_code": 200,
    "request_datetime": "2026-05-18T14:32:01.123456",
    "curl": "curl -X PATCH \"http://localhost:9876/web-bff/users/me/loyalty/status\" -H \"Content-Type: application/json\" -d '{\"action\": \"welcomeModalClosed\", \"value\": true}'",
    "prev_status": "ENROLLED",
    "prev_action": "DISPLAYWELCOMEMODAL",
    "operation": "STATUS",
    "action": "welcomeModalClosed",
    "new_status": "ENROLLED",
    "new_action": "NONE"
  }
]
```

```
📨  GET /log
📤  Retornando 12 entradas del log
```

---

### DELETE `/log`

Vacía el archivo `server.log`. No elimina el archivo, solo borra su contenido. Emite el evento SSE `log-cleared` a todos los clientes conectados para que limpien su vista de log.

**Response 200:**
```json
{ "status": { "status": "OK", "statusCode": 0, "successMessage": "Log cleared" } }
```

```
🗑️   DELETE /log
✅  server.log vaciado
```

---

### GET `/events`

Endpoint SSE (_Server-Sent Events_). El cliente se conecta una vez y el servidor le envía eventos en tiempo real sin necesidad de polling.

**Tipos de evento:**

| Evento | Cuándo se emite | Payload |
|---|---|---|
| `log-entry` | Tras cualquier operación (excepto GET /log) | JSON del log entry completo |
| `log-cleared` | Tras DELETE /log | `{}` |

El cliente usa los eventos para:
- Prepender nuevas entradas al panel de log sin refetch.
- Auto-refrescar el estado de membresía cuando llega un cambio de estado (`new_status` presente) o un enroll exitoso.
- Limpiar su panel de log al recibir `log-cleared`.

El servidor mantiene la conexión viva con comentarios de keepalive cada 20 s. Si la conexión se corta, el browser reconecta automáticamente.

```
📡  SSE client conectado  (1 activo)
📡  SSE client desconectado (0 activos)
```

---

### GET `/<base>/users/me/loyalty/status`

Devuelve el contenido actual de `states/current_state.json` e imprime en consola el status y action del estado actual.

```
📨  GET /pocket-bff/users/me/loyalty/status
  ┌───────────────────────────────────────────────────────────────────────────────┐
  │  STATUS      →  status = ENROLLED    , action = NONE                         │
  └───────────────────────────────────────────────────────────────────────────────┘
📤  Retornando current_state.json
```

---

### GET `/<base>/users/me/loyalty/coupons`

Devuelve `responses/get_loyalty_coupons_enrolled_{COUPONS_LIST_SUFFIX}.json`.

Para cambiar la respuesta, edita `COUPONS_LIST_SUFFIX` en `.env` y reinicia el servidor (o usa `PUT /configuration`):

```env
COUPONS_LIST_SUFFIX=full          # lista completa
COUPONS_LIST_SUFFIX=empty         # lista vacía
COUPONS_LIST_SUFFIX=server_error  # error de servidor (código HTTP del archivo)
COUPONS_LIST_SUFFIX=bad_request       # bad request (código HTTP del archivo)
COUPONS_LIST_SUFFIX=200_status_error  # HTTP 200 pero status de error en el body
```

```
📨  GET /pocket-bff/users/me/loyalty/coupons  [suffix=full]
📤  Retornando get_loyalty_coupons_enrolled_full.json
```

---

### GET `/<base>/users/me/loyalty/coupons/redeemed`

Devuelve `responses/get_loyalty_coupons_redeemed_{COUPONS_REDEEMED_SUFFIX}.json`.

Para cambiar entre lista vacía y lista completa, edita `COUPONS_REDEEMED_SUFFIX` en `.env` y reinicia el servidor:

```env
COUPONS_REDEEMED_SUFFIX=full
```

```
📨  GET /pocket-bff/users/me/loyalty/coupons/redeemed  [suffix=full]
📤  Retornando get_loyalty_coupons_redeemed_full.json
```

---

### GET `/<base>/checkout/coupons?isBuyNow=<bool>`

Devuelve `responses/get_checkout_coupons_{CHECKOUT_COUPONS_SUFFIX}.json`.

El parámetro `isBuyNow` es **obligatorio**. Si no se incluye, el servidor responde 400.

**Response 400** (parámetro faltante):
```json
{
  "status": { "status": "ERROR", "statusCode": 400, "successMessage": "Missing required parameter: isBuyNow" }
}
```

Para cambiar el archivo servido, edita `CHECKOUT_COUPONS_SUFFIX` en `.env` y reinicia el servidor:

```env
CHECKOUT_COUPONS_SUFFIX=no_cart_error
```

```
📨  GET /pocket-bff/checkout/coupons?isBuyNow=false  [isBuyNow=false]  [suffix=cart]
📤  Retornando get_checkout_coupons_cart.json
```

---

### GET `/<base>/loyalty/cancel-reasons`

Devuelve el contenido de `responses/get_loyalty_cancel_reasons.json` sin ningún parámetro adicional.

```
📨  GET /pocket-bff/loyalty/cancel-reasons
📤  Retornando get_loyalty_cancel_reasons.json
```

---

### POST `/<base>/users/me/loyalty/enroll`

Enrola o re-enrola al usuario. El comportamiento depende del valor actual de `loyaltyData.status` en `current_state.json`.

#### Caso: `loyaltyStatus = notEnrolled` o `declined`

Valida que el body contenga los campos requeridos, actualiza `current_state.json` y retorna 200.

**Body requerido:**
```json
{
  "firstName": "Jesus",
  "lastName": "Guzman",
  "motherLastName": "Mondragon",
  "gender": "M",
  "dateOfBirth": "01/01/1990"
}
```

**Response 200:**
```json
{
  "status": { "status": "OK", "statusCode": 0 },
  "data": {
    "loyaltyMemberId": "720100015844",
    "userId": 2465729859,
    "action": "displayWelcomeModal",
    "loyaltyStatus": "enrolled",
    "memberSince": "2026-05-18"
  }
}
```

**Response 400** (campos faltantes):
```json
{
  "status": { "status": "ERROR", "statusCode": 400, "successMessage": "Update data not received" }
}
```

Tras el enroll exitoso, `current_state.json` se actualiza con:
- `firstName`, `lastName`, `maternalName`, `dateOfBirth` del body
- `loyaltyData.action = displayWelcomeModal`
- `loyaltyData.status = enrolled`
- `loyaltyData.memberSince = yyyy-mm-dd`

```
📨  POST /pocket-bff/users/me/loyalty/enroll  [loyaltyStatus=notEnrolled]
✅  current_state.json actualizado → enrolled / displayWelcomeModal
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │  BEFORE            →  status = NOTENROLLED  , action = DISPLAYENROLLMODAL              │
  │  ENROLL ACTION     →  enroll                                                           │
  │  AFTER             →  status = ENROLLED     , action = DISPLAYWELCOMEMODAL             │
  └─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Caso: `loyaltyStatus = unenrolled`

Valida que el body esté vacío `{}`, actualiza `current_state.json` y retorna 200.

**Body requerido:** `{}` (vacío)

**Response 200:** misma estructura que el caso anterior.

```
📨  POST /pocket-bff/users/me/loyalty/enroll  [loyaltyStatus=unenrolled]
✅  current_state.json actualizado → enrolled / displayWelcomeModal
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │  BEFORE            →  status = UNENROLLED   , action = NONE                            │
  │  ENROLL ACTION     →  reenroll                                                         │
  │  AFTER             →  status = ENROLLED     , action = DISPLAYWELCOMEMODAL             │
  └─────────────────────────────────────────────────────────────────────────────────────────┘
```

**Response 400** (body no vacío):
```json
{
  "status": { "status": "ERROR", "statusCode": 400, "successMessage": "Body is not empty" }
}
```

#### Caso: cualquier otro `loyaltyStatus`

**Response 409:**
```json
{
  "status": { "status": "ERROR", "statusCode": 409, "successMessage": "invalid operation, current membership {status}" }
}
```

---

### PATCH `/<base>/users/me/loyalty/status`

Recibe un body JSON con `action` y `value`, aplica la transición de estado correspondiente y devuelve el response del escenario.

**Body esperado:**
```json
{ "action": "<action>", "value": true }
```

> **Regla especial — `unenroll`:** se aplican dos validaciones previas en orden:
>
> 1. **Estado actual no es `enrolled`** → responde 409 antes de verificar cualquier otro campo:
>    ```json
>    { "status": { "status": "ERROR", "statusCode": 409, "successMessage": "invalid operation, current membership is not enrolled" } }
>    ```
> 2. **Campo `cancelReason` faltante o no string** → responde 400:
>    ```json
>    { "status": { "status": "ERROR", "statusCode": 400, "successMessage": "cancelReason do not received" } }
>    ```

**Escenarios disponibles:**

| `action` | `value` | Estado siguiente | Respuesta |
|---|---|---|---|
| `displayWelcomeModal` | `true` | `enrolled_welcome_state` | `path_status_enroll_welcome` |
| `displayEnrollModal` | `true` | `notEnrolled_enroll_state` | `path_status_notEnrolled_enroll` |
| `welcomeModalClosed` | `true` | `enrolled_none_state` | `path_status_enrolled` |
| `enrollModalClosed` | `true` | `declined_none_state` | `path_status_declined` |
| `unenroll` | `true` | `unenrolled_none_state` | `path_status_unenroll` |

Si el `action` no coincide con ningún escenario, el servidor responde `200` con `"No scenario matched"` y **no modifica** `current_state.json`.

```
📨  PATCH /pocket-bff/users/me/loyalty/status → action='welcomeModalClosed', value=True
✅  enrolled_none_state.json  →  current_state.json
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │  BEFORE            →  status = NOT_ENROLLED , action = DISPLAYENROLLMODAL              │
  │  STATUS ACTION     →  welcomeModalClosed                                               │
  │  AFTER             →  status = ENROLLED     , action = NONE                            │
  └─────────────────────────────────────────────────────────────────────────────────────────┘
📤  Retornando path_status_enrolled.json
```

---

## Cliente web

El directorio `client/` incluye una interfaz HTML que permite interactuar con el servidor sin necesidad de Postman o curl.

```bash
# Con el servidor corriendo, abre directamente en el browser:
open client/index.html
```

Consulta **[client/README.md](client/README.md)** para ver la documentación completa del cliente.

---

## Reiniciar el estado manualmente

```bash
# Volver a notEnrolled (estado inicial)
cp states/notEnrolled_enroll_state.json states/current_state.json

# Cualquier otro estado
cp states/enrolled_welcome_state.json states/current_state.json
```

---

## Delay de respuesta — `DELAY_MS`

Cuando `DELAY_MS > 0`, el servidor espera ese número de milisegundos antes de responder. Útil para simular latencia de red.

El delay **no aplica** en los siguientes casos:
- Path `/log` o `/configuration`
- Request que incluya el header `server_delay: false`

El cliente web envía `server_delay: false` en las llamadas internas que no deben verse afectadas por el delay configurado (refresco automático del header de status y carga de razones de cancelación).

---

## Supresión del log — header `server-log: false`

Cualquier request que incluya el header `server-log: false` es procesado con normalidad pero **no se registra en `server.log`** y no emite evento SSE `log-entry`.

El cliente web usa este mecanismo en dos llamadas internas para evitar contaminar el panel de log:

- `GET /<base>/users/me/loyalty/status` (refresco automático del header)
- `GET /<base>/loyalty/cancel-reasons` (carga del selector de razones)

---

## Código HTTP de archivos de respuesta

El servidor extrae el código HTTP de la **primera línea** de cada archivo en `responses/` y lo usa como código de respuesta real:

```
HTTP/1.1 200 OK          →  responde 200
HTTP/1.1 404 Not Found   →  responde 404
```

Si el archivo no contiene cabecera HTTP (solo JSON), el servidor usa `200` como fallback. Esto permite simular errores simplemente editando la primera línea de un archivo de respuesta.

---

## server.log

Cada request recibido por el servidor queda registrado como una línea JSONL en `server.log` (salvo los que incluyan `server-log: false`):

```json
{
  "method": "GET",
  "path": "/web-bff/users/me/loyalty/status",
  "http_code": 200,
  "request_datetime": "2026-05-18T14:32:01.123456",
  "curl": "curl -X GET \"http://localhost:9876/web-bff/users/me/loyalty/status\""
}
```

Los requests de transición de estado y enrolamiento incluyen campos adicionales: `prev_status`, `prev_action`, `operation`, `action`, `new_status`, `new_action`.

Usa `GET /log` para consultarlo desde el cliente o `DELETE /log` para vaciarlo.

---

## Cómo funciona

```
GET/PUT /configuration
        │
        ▼
  loyalty_server.py → config_handler.py
        ├─ GET → devuelve VERSION + CONFIG + paths()
        └─ PUT → actualiza CONFIG en memoria, devuelve estado actualizado

─────────────────────────────────────────────

GET/DELETE /log
        │
        ▼
  loyalty_server.py → log_handler.py
        ├─ GET    → lee server.log, retorna array JSON (más reciente primero)
        └─ DELETE → vacía server.log + push evento "log-cleared" vía SSE

─────────────────────────────────────────────

GET /events  (SSE)
        │
        ▼
  loyalty_server.py → events_handler.py
        ├─ Mantiene conexión abierta (keepalive cada 20 s)
        ├─ Cada _respond() llama push_log_entry(entry)
        │    ├─ GET /log  → no notifica (cliente leyendo su propio log)
        │    ├─ DELETE /log → emite evento "log-cleared"
        │    └─ resto    → emite evento "log-entry" con el JSON del entry
        └─ El browser reconecta automáticamente si pierde la conexión

─────────────────────────────────────────────

App → GET /<base>/users/me/loyalty/status
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → status_handler.py
        └─ Lee y retorna current_state.json
        │
        ▼
App ← estado actual de lealtad

─────────────────────────────────────────────

App → GET /<base>/users/me/loyalty/coupons
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → coupons_handler.py
        └─ resolve_response_file → get_loyalty_coupons_enrolled_{suffix}.json
        │
        ▼
App ← lista de cupones (empty | full)

─────────────────────────────────────────────

App → GET /<base>/users/me/loyalty/coupons/redeemed
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → coupons_handler.py
        └─ resolve_response_file → get_loyalty_coupons_redeemed_{suffix}.json
        │
        ▼
App ← lista de cupones canjeados (empty | full)

─────────────────────────────────────────────

App → GET /<base>/checkout/coupons?isBuyNow=false
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → coupons_handler.py
        ├─ Valida presencia de parámetro isBuyNow → 400 si falta
        └─ resolve_response_file → get_checkout_coupons_{suffix}.json
        │
        ▼
App ← cupones de checkout (cart | no_cart_error)

─────────────────────────────────────────────

App → GET /<base>/loyalty/cancel-reasons
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → status_handler.py
        └─ resolve_response_file → get_loyalty_cancel_reasons.json
        │
        ▼
App ← lista de razones de cancelación

─────────────────────────────────────────────

App → POST /<base>/users/me/loyalty/enroll
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → enroll_handler.py
        ├─ Lee loyaltyData.status de current_state.json
        ├─ notEnrolled/declined → valida body, actualiza current_state.json
        ├─ unenrolled           → valida body vacío, actualiza current_state.json
        └─ otro status          → retorna 409
        │
        ▼
App ← response de enroll con loyaltyMemberId, userId, memberSince

─────────────────────────────────────────────

App → PATCH /<base>/users/me/loyalty/status
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → status_handler.py
        ├─ Lee action + value del body
        ├─ unenroll → valida status actual == enrolled → 409 si no
        ├─ unenroll → valida cancelReason (string) → 400 si falta
        ├─ Busca en SCENARIOS
        ├─ Copia state_X.json → current_state.json
        └─ resolve_response_file → path_status_X.json
        │
        ▼
App ← response del PATCH con nuevo estado
```
