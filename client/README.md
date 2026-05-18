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

## Pantalla principal

### Header sticky

Siempre visible en la parte superior. Muestra de un vistazo el estado de la membresía actual:

| Elemento | Descripción |
|---|---|
| Badge de status | Color según estado: verde = `enrolled`, naranja = `notEnrolled`, gris = `unenrolled`, rojo = `declined` |
| Badge de acción | Acción pendiente del servidor (`none`, `displayWelcomeModal`, `displayEnrollModal`) |
| Miembro desde | Fecha de alta en el programa de lealtad |
| Nombre del usuario | `firstName` + `lastName` del estado actual |

El botón **Actualizar** recarga el estado desde `GET /<base>/users/me/loyalty/status`.

### Card — Estado de Lealtad

Muestra los campos de `loyaltyData`: estado, acción y fecha de membresía.

### Card — Datos del Usuario

Muestra los campos personales del `current_state.json`: nombre, apellidos, género, email, fecha de nacimiento, ID de repositorio y número de monedero.

---

## Panel de configuración

Se abre y cierra con el botón **⚙️ Config** del header (queda resaltado en azul cuando está visible).  
También se puede cerrar haciendo clic en el backdrop semitransparente o en el botón **✕**.

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
| `index.html` | Estructura, estilos CSS y markup del panel |
| `index.js` | Lógica: fetch, render, dirty-state, panel toggle |
