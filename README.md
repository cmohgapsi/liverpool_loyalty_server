# Proxyman — Mock de flujo de Lealtad

Servidor local que intercepta llamadas redirigidas por Proxyman (Map Remote) para simular las transiciones de estado del sistema de lealtad, sin tocar ninguna regla de Proxyman en tiempo de ejecución.

Atiende siete endpoints:

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/pocket-bff/users/me/loyalty/status` | Devuelve `current_state.json` |
| `GET` | `/pocket-bff/users/me/loyalty/coupons` | Devuelve lista de cupones según `COUPONS_LIST_SUFFIX` |
| `GET` | `/pocket-bff/users/me/loyalty/coupons/redeemed` | Devuelve cupones canjeados según `COUPONS_REDEEMED_SUFFIX` |
| `GET` | `/pocket-bff/checkout/coupons?isBuyNow=<bool>` | Devuelve cupones de checkout según `CHECKOUT_COUPONS_SUFFIX` |
| `GET` | `/pocket-bff/loyalty/cancel-reasons` | Devuelve `get_loyalty_cancel_reasons.json` |
| `POST` | `/pocket-bff/users/me/loyalty/enroll` | Enrola o re-enrola al usuario según su estado actual |
| `PATCH` | `/pocket-bff/users/me/loyalty/status` | Aplica transición de estado y devuelve el response correspondiente |

---

## Estructura de archivos

```
decommission/
├── documentation/
│   ├── LIVERPOOL-DECOMMISSION.postman_collection.json  ← Colección Postman con los endpoints
│   └── LoyaltyStatus.png                               ← Diagrama de estados de lealtad
├── states/
│   ├── current_state.json              ← Estado actual (leído y modificado por varios endpoints)
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
│   ├── path_status_unenroll.json
│   ├── get_loyalty_coupons_enrolled_empty.json
│   ├── get_loyalty_coupons_enrolled_full.json
│   ├── get_loyalty_coupons_redeemed_empty.json
│   ├── get_loyalty_coupons_redeemed_full.json
│   ├── get_checkout_coupons_cart.json
│   ├── get_checkout_coupons_no_cart_error.json
│   └── get_loyalty_cancel_reasons.json
├── .env                                ← Variables de entorno (no versionado, créalo desde .env-example)
├── .env-example                        ← Plantilla de variables de entorno
├── loyalty_server.py                   ← Servidor local: routing y configuración
├── coupons_handler.py                  ← Handler y lógica de cupones (CouponsHandlerMixin)
├── enroll_handler.py                   ← Handler y lógica de enrolamiento (EnrollHandlerMixin)
├── status_handler.py                   ← Handler y lógica de status (StatusHandlerMixin, SCENARIOS)
├── state_utils.py                      ← Utilidades compartidas (load_env, extract_json_body, read_current_status, print_operation_result)
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
BASE_PATH=/ruta/absoluta/a/decommission
PORT=9876
TARGET_PATH=/pocket-bff/users/me/loyalty/status
TARGET_COUPONS_PATH=/pocket-bff/users/me/loyalty/coupons
COUPONS_LIST_SUFFIX=empty
TARGET_REDEEMED_PATH=/pocket-bff/users/me/loyalty/coupons/redeemed
COUPONS_REDEEMED_SUFFIX=empty
TARGET_ENROLL_PATH=/pocket-bff/users/me/loyalty/enroll
LOYALTY_MEMBER_ID=720100015844
USER_ID=2465729859
TARGET_CHECKOUT_COUPONS_PATH=/pocket-bff/checkout/coupons
CHECKOUT_COUPONS_SUFFIX=cart
TARGET_CANCEL_REASONS_PATH=/pocket-bff/loyalty/cancel-reasons
```

| Variable | Valores | Descripción |
|---|---|---|
| `BASE_PATH` | ruta absoluta | Ruta a la carpeta `decommission/`. Ajústala si mueves el proyecto. |
| `PORT` | `9876` | Puerto del servidor local. |
| `TARGET_PATH` | path | Endpoint de loyalty status (GET y PATCH). |
| `TARGET_COUPONS_PATH` | path | Endpoint de lista de cupones (GET). |
| `COUPONS_LIST_SUFFIX` | `empty` · `full` | Archivo de cupones a servir. |
| `TARGET_REDEEMED_PATH` | path | Endpoint de cupones canjeados (GET). |
| `COUPONS_REDEEMED_SUFFIX` | `empty` · `full` | Archivo de cupones canjeados a servir. |
| `TARGET_ENROLL_PATH` | path | Endpoint de enrolamiento (POST). |
| `LOYALTY_MEMBER_ID` | string | ID de miembro de lealtad retornado en el response de enroll. |
| `USER_ID` | número | ID de usuario retornado en el response de enroll. |
| `TARGET_CHECKOUT_COUPONS_PATH` | path | Endpoint de cupones de checkout (GET). |
| `CHECKOUT_COUPONS_SUFFIX` | `cart` · `no_cart_error` | Archivo de cupones de checkout a servir. |
| `TARGET_CANCEL_REASONS_PATH` | path | Endpoint de razones de cancelación (GET). |

---

## Setup en Proxyman

### Map Remote — Lealtad (loyalty)

**Match URL** (regex):
```
^\/pocket-bff\/(users\/me\/loyalty\/.*|checkout\/coupons|loyalty\/cancel-reasons)
```

**Método:** `ANY`

**Redirect to:**
```
http://localhost:9876/pocket-bff/*
```

---

## Cómo ejecutar

```bash
python3 /ruta/a/decommission/loyalty_server.py
```

Salida esperada:

```
🚀  Loyalty server corriendo en http://localhost:9876
📁  States:    …/states
📁  Responses: …/responses
🌐  GET  /pocket-bff/users/me/loyalty/status
🌐  GET  /pocket-bff/users/me/loyalty/coupons  [suffix=full]
🌐  GET  /pocket-bff/users/me/loyalty/coupons/redeemed  [suffix=empty]
🌐  GET  /pocket-bff/checkout/coupons?isBuyNow=<bool>  [suffix=cart]
🌐  GET  /pocket-bff/loyalty/cancel-reasons
🌐  POST  /pocket-bff/users/me/loyalty/enroll
🌐  PATCH /pocket-bff/users/me/loyalty/status
```

> Mantén esta terminal abierta durante toda la sesión de prueba.

---

## Endpoints

### GET `/pocket-bff/users/me/loyalty/status`

Devuelve el contenido actual de `states/current_state.json` e imprime en consola el status y action del estado actual.

```
📨  GET /pocket-bff/users/me/loyalty/status
  ┌───────────────────────────────────────────────────────────────────────────────┐
  │  STATUS      →  status = ENROLLED    , action = NONE                         │
  └───────────────────────────────────────────────────────────────────────────────┘
📤  Retornando current_state.json
```

---

### GET `/pocket-bff/users/me/loyalty/coupons`

Devuelve `responses/get_loyalty_coupons_enrolled_{COUPONS_LIST_SUFFIX}.json`.

Para cambiar entre lista vacía y lista completa, edita `COUPONS_LIST_SUFFIX` en `.env` y reinicia el servidor:

```env
COUPONS_LIST_SUFFIX=full
```

```
📨  GET /pocket-bff/users/me/loyalty/coupons  [suffix=full]
📤  Retornando get_loyalty_coupons_enrolled_full.json
```

---

### GET `/pocket-bff/users/me/loyalty/coupons/redeemed`

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

### GET `/pocket-bff/checkout/coupons?isBuyNow=<bool>`

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

### GET `/pocket-bff/loyalty/cancel-reasons`

Devuelve el contenido de `responses/get_loyalty_cancel_reasons.json` sin ningún parámetro adicional.

```
📨  GET /pocket-bff/loyalty/cancel-reasons
📤  Retornando get_loyalty_cancel_reasons.json
```

---

### POST `/pocket-bff/users/me/loyalty/enroll`

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

### PATCH `/pocket-bff/users/me/loyalty/status`

Recibe un body JSON con `action` y `value`, aplica la transición de estado correspondiente y devuelve el response del escenario.

**Body esperado:**
```json
{ "action": "<action>", "value": true }
```

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

## Reiniciar el estado manualmente

```bash
# Volver a notEnrolled (estado inicial)
cp states/notEnrolled_enroll_state.json states/current_state.json

# Cualquier otro estado
cp states/enrolled_welcome_state.json states/current_state.json
```

---

## Cómo funciona

```
App → GET /pocket-bff/users/me/loyalty/status
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

App → GET /pocket-bff/users/me/loyalty/coupons
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → coupons_handler.py
        └─ Lee get_loyalty_coupons_enrolled_{COUPONS_LIST_SUFFIX}.json
        │
        ▼
App ← lista de cupones (empty | full)

─────────────────────────────────────────────

App → GET /pocket-bff/users/me/loyalty/coupons/redeemed
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → coupons_handler.py
        └─ Lee get_loyalty_coupons_redeemed_{COUPONS_REDEEMED_SUFFIX}.json
        │
        ▼
App ← lista de cupones canjeados (empty | full)

─────────────────────────────────────────────

App → GET /pocket-bff/checkout/coupons?isBuyNow=false
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → coupons_handler.py
        ├─ Valida presencia de parámetro isBuyNow → 400 si falta
        └─ Lee get_checkout_coupons_{CHECKOUT_COUPONS_SUFFIX}.json
        │
        ▼
App ← cupones de checkout (cart | no_cart_error)

─────────────────────────────────────────────

App → GET /pocket-bff/loyalty/cancel-reasons
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → status_handler.py
        └─ Lee get_loyalty_cancel_reasons.json
        │
        ▼
App ← lista de razones de cancelación

─────────────────────────────────────────────

App → POST /pocket-bff/users/me/loyalty/enroll
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

App → PATCH /pocket-bff/users/me/loyalty/status
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py → status_handler.py
        ├─ Lee action + value del body
        ├─ Busca en SCENARIOS
        ├─ Copia state_X.json → current_state.json
        └─ Retorna responses/path_status_X.json
        │
        ▼
App ← response del PATCH con nuevo estado
```
