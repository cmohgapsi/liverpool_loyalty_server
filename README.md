# Proxyman — Mock de flujo de Lealtad

Servidor local que intercepta llamadas redirigidas por Proxyman (Map Remote) para simular las transiciones de estado del sistema de lealtad, sin tocar ninguna regla de Proxyman en tiempo de ejecución.

Atiende tres endpoints:

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/pocket-bff/users/me/loyalty/status` | Devuelve `current_state.json` |
| `GET` | `/pocket-bff/loyalty/coupons` | Devuelve lista de cupones según `COUPONS_LIST_SUFFIX` |
| `PATCH` | `/pocket-bff/users/me/loyalty/status` | Aplica transición de estado y devuelve el response correspondiente |

---

## Estructura de archivos

```
decommission/
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
├── loyalty_server.py                   ← Servidor local
├── state_utils.py                      ← Utilidades compartidas de estado
└── README.md
```

---

## Requisitos

- macOS con **Proxyman** instalado
- **Python 3** (incluido en macOS por defecto)
- La carpeta copiada en tu máquina (ajusta `BASE_PATH` en `loyalty_server.py` si la mueves)

---

## Configuración

### Variables globales en `loyalty_server.py`

| Variable | Valores | Descripción |
|---|---|---|
| `BASE_PATH` | ruta absoluta | Directorio raíz de la carpeta `decommission/` |
| `PORT` | `9876` | Puerto del servidor local |
| `COUPONS_LIST_SUFFIX` | `"empty"` · `"full"` | Controla qué archivo de cupones se sirve en el GET `/loyalty/coupons` |

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
| Match URL | `https://<host>/pocket-bff/loyalty/coupons` |
| Método | `GET` |
| Redirect to | `http://localhost:9876/pocket-bff/loyalty/coupons` |

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

### GET `/pocket-bff/loyalty/coupons`

Devuelve `responses/get_loyalty_coupons_enrolled_{COUPONS_LIST_SUFFIX}.json`.

Para cambiar entre lista vacía y lista completa, edita la variable en `loyalty_server.py`:

```python
COUPONS_LIST_SUFFIX = "empty"  # "empty" | "full"
```

```
📨  GET /pocket-bff/loyalty/coupons  [suffix=full]
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

App → GET /pocket-bff/loyalty/coupons
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
