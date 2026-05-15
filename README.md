# Proxyman — Mock de flujo de Lealtad

Servidor local que intercepta llamadas redirigidas por Proxyman (Map Remote) para simular las transiciones de estado del sistema de lealtad, sin tocar ninguna regla de Proxyman en tiempo de ejecución.

Atiende tres endpoints:

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/pocket-bff/users/me/loyalty/status` | Devuelve `current_state.json` |
| `GET` | `/pocket-bff/users/me/loyalty/coupons` | Devuelve lista de cupones según `COUPONS_LIST_SUFFIX` |
| `PATCH` | `/pocket-bff/users/me/loyalty/status` | Aplica transición de estado y devuelve el response correspondiente |

---

## Estructura de archivos

```
decommission/
├── documentation/
│   ├── LIVERPOOL-DECOMMISSION.postman_collection.json  ← Colección Postman con los endpoints
│   └── LoyaltyStatus.png                               ← Diagrama de estados de lealtad
├── states/
│   ├── current_state.json              ← Estado actual (leído por el GET de status)
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
│   └── get_loyalty_coupons_enrolled_full.json
├── .env                                ← Rutas configurables (no versionado, créalo desde .env-example)
├── .env-example                        ← Plantilla de variables de entorno
├── loyalty_server.py                   ← Servidor local: routing y configuración
├── coupons_handler.py                  ← Handler y lógica de cupones (CouponsHandlerMixin)
├── status_handler.py                   ← Handler y lógica de status (StatusHandlerMixin, SCENARIOS)
├── state_utils.py                      ← Utilidades compartidas (load_env, extract_json_body, read_current_status)
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
TARGET_COUPONS_PATH=/pocket-bff/loyalty/coupons
COUPONS_LIST_SUFFIX=empty
```

| Variable | Valores | Descripción |
|---|---|---|
| `BASE_PATH` | ruta absoluta | Ruta a la carpeta `decommission/`. Ajústala si mueves el proyecto. |
| `PORT` | `9876` | Puerto del servidor local. |
| `TARGET_PATH` | path | Endpoint de loyalty status (GET y PATCH). |
| `TARGET_COUPONS_PATH` | path | Endpoint de cupones (GET). |
| `COUPONS_LIST_SUFFIX` | `empty` · `full` | Controla qué archivo de cupones se sirve. |

---

## Setup en Proxyman

### Map Remote — GET de loyalty status

| Campo | Valor |
|---|---|
| Match URL | `https://<host>/pocket-bff/users/me/loyalty/status` |
| Método | `GET` |
| Redirect to | `http://localhost:9876/pocket-bff/users/me/loyalty/status` |

### Map Remote — GET de cupones

| Campo | Valor |
|---|---|
| Match URL | `https://<host>/pocket-bff/users/me/loyalty/coupons` |
| Método | `GET` |
| Redirect to | `http://localhost:9876/pocket-bff/users/me/loyalty/coupons` |

### Map Remote — PATCH de estado de lealtad

| Campo | Valor |
|---|---|
| Match URL | `https://<host>/pocket-bff/users/me/loyalty/status` |
| Método | `PATCH` |
| Redirect to | `http://localhost:9876/pocket-bff/users/me/loyalty/status` |

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
🌐  TARGET_PATH         = /pocket-bff/users/me/loyalty/status
🌐  TARGET_COUPONS_PATH = /pocket-bff/loyalty/coupons
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

Salida en consola tras una transición exitosa:

```
📨  PATCH /pocket-bff/users/me/loyalty/status → action='welcomeModalClosed', value=True
✅  enrolled_none_state.json  →  current_state.json
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │  BEFORE            →  status = NOT_ENROLLED , action = DISPLAYENROLLMODAL              │
  │  PATH ACTION       →  welcomeModalClosed                                               │
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
  loyalty_server.py
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
  loyalty_server.py
        └─ Lee get_loyalty_coupons_enrolled_{COUPONS_LIST_SUFFIX}.json
        │
        ▼
App ← lista de cupones (empty | full)

─────────────────────────────────────────────

App → PATCH /pocket-bff/users/me/loyalty/status
        │
        ▼
  Proxyman Map Remote → localhost:9876
        │
        ▼
  loyalty_server.py
        ├─ Lee action + value del body
        ├─ Busca en SCENARIOS
        ├─ Copia state_X.json → current_state.json
        └─ Retorna responses/path_status_X.json
        │
        ▼
App ← response del PATCH con nuevo estado
```
