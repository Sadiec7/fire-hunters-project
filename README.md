# Fire Hunters Project

Proyecto integral que incluye Backend (Node.js + Express + SQLite) y Frontend (Angular).

---

## Ejecución con Un Solo Comando

Para levantar toda la aplicación (Backend + Frontend) **sin configurar nada adicional**, abre tu terminal en la raíz del proyecto y ejecuta:

```bash
docker compose up --build
```

*(Si utilizas una versión previa de Docker Compose, puedes usar `docker-compose up --build`)*.

¡Listo! No necesitas instalar Node, ni ejecutar `npm install`, ni configurar bases de datos manualmente. Docker se encarga de todo de forma automática.

---

## URLs de Acceso

Una vez ejecutado el comando, accede a las aplicaciones desde tu navegador:

| Servicio | URL | Descripción |
| :--- | :--- | :--- |
| **Frontend** | [http://localhost:4200](http://localhost:4200) | Interfaz web en Angular (con Hot Reload) |
| **Backend API** | [http://localhost:3000](http://localhost:3000) | API Express con SQLite conectada |

---

## Detener la Aplicación

Para apagar los contenedores:
- Presiona `Ctrl + C` en la terminal donde está corriendo el comando.
- O ejecuta en otra terminal dentro de la raíz:
  ```bash
  docker compose down
  ```

---

## Características Incluidas

- **Cero configuración manual**: Las dependencias se instalan automáticamente dentro de los contenedores Linux.
- **Recarga en vivo (Live Reload / Hot Reload)**: Cualquier cambio que hagas en los archivos de `front/src` o `back/` se detectará y actualizará automáticamente sin reiniciar Docker.
- **Aislamiento de `node_modules`**: Se configuran volúmenes anónimos y `.dockerignore` para evitar conflictos entre los módulos nativos de Windows y el entorno Linux del contenedor.
- **Persistencia de SQLite**: La base de datos SQLite se almacena automáticamente en tu carpeta local `back/` para conservar los datos entre reinicios.

---

## Requisitos Previos

- Tener instalado **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** y tenerlo abierto/iniciado en tu equipo.
