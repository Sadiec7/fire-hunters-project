# 🔥 Fire Hunters Project

Proyecto integral con arquitectura en contenedores Docker:
- **Base de Datos**: PostgreSQL 16
- **Backend**: Node.js + Express + `pg` (Pool de conexiones)
- **Frontend**: Angular (con Hot Reload / Live Reload)

---

## 🚀 Ejecución con Un Solo Comando

Para levantar toda la aplicación (Base de Datos PostgreSQL + Backend + Frontend) **sin configurar nada adicional**, abre tu terminal en la raíz del proyecto y ejecuta:

```bash
docker compose up --build
```

*(Si utilizas una versión anterior de Docker Compose: `docker-compose up --build`)*.

Al ejecutar este comando:
1. Se inicia y configura el contenedor de **PostgreSQL**.
2. El contenedor de **Backend** espera a que PostgreSQL esté 100% listo (`healthcheck`) para iniciar y conectarse automáticamente.
3. El contenedor de **Frontend** arranca en modo desarrollo con recarga en vivo.

---

## 🌐 Servicios y URLs de Acceso

| Servicio | URL / Host | Credenciales / Puerto | Descripción |
| :--- | :--- | :--- | :--- |
| **Frontend** | [http://localhost:4200](http://localhost:4200) | Puerto `4200` | Interfaz web en Angular |
| **Backend API** | [http://localhost:3000](http://localhost:3000) | Puerto `3000` | API Express |
| **Test Base de Datos** | [http://localhost:3000/db-status](http://localhost:3000/db-status) | Puerto `3000` | Endpoint para verificar el estado de PostgreSQL |
| **PostgreSQL** | `localhost:5433` | User: `postgres`<br>Password: `postgres`<br>DB: `fire_hunters_db` | Servidor de base de datos relacional (puerto 5433 para evitar colisión con Postgres local) |

---

## 🐘 Cómo Configurar la Conexión a PostgreSQL

La conexión es flexible y admite tanto **variables individuales** como una **URL completa (`DATABASE_URL`)**.

### 1. Conexión automática por defecto (en Docker)
En `docker-compose.yml`, el backend ya viene preconfigurado para conectarse al servicio `postgres`:

```yaml
environment:
  - PORT=3000
  - DB_HOST=postgres
  - DB_PORT=5432
  - DB_USER=postgres
  - DB_PASSWORD=postgres
  - DB_NAME=fire_hunters_db
```

### 2. Conectar a un PostgreSQL Externo o Remoto (Supabase, Neon, AWS RDS, etc.)
Si deseas conectar el backend a una base de datos externa en la nube o en tu máquina física:

#### Opción A: Mediante URL completa (`DATABASE_URL`)
Edita la sección `environment` de `backend` en `docker-compose.yml` (o en tu archivo `back/.env` si ejecutas sin Docker):

```yaml
environment:
  - DATABASE_URL=postgresql://usuario:contraseña@servidor.com:5432/nombre_bd?sslmode=require
```

#### Opción B: Mediante variables individuales
```yaml
environment:
  - DB_HOST=tu-servidor-remoto.com
  - DB_PORT=5432
  - DB_USER=tu_usuario
  - DB_PASSWORD=tu_contraseña
  - DB_NAME=tu_base_de_datos
```

### 3. Conectarte a la base de datos desde tu PC (DBeaver, TablePlus, pgAdmin, VS Code)
Como el puerto `5433` está expuesto a tu máquina (para evitar colisión si ya tienes otro PostgreSQL instalado en el 5432), puedes conectarte con cualquier gestor de bases de datos usando estos datos:

- **Host**: `localhost` (o `127.0.0.1`)
- **Puerto**: `5433`
- **Usuario**: `postgres`
- **Contraseña**: `postgres`
- **Base de datos**: `fire_hunters_db`
- **Cadena de conexión directa**: `postgresql://postgres:postgres@localhost:5433/fire_hunters_db`

### 4. Ejecución local del Backend sin Docker
Si necesitas ejecutar solo el backend fuera de Docker (`cd back && npm start`):
1. Copia el archivo de ejemplo:
   ```bash
   cp back/.env.example back/.env
   ```
2. Modifica los valores en `back/.env` según tu base de datos local.
3. Ejecuta `npm start`.

---

## 🛑 Detener los Contenedores

Para apagar todos los servicios:
- Presiona `Ctrl + C` en la terminal donde se ejecutan los contenedores.
- O ejecuta en otra terminal en la raíz del proyecto:
  ```bash
  docker compose down
  ```

> [!TIP]
> **Persistencia de Datos**: Los datos de PostgreSQL se guardan en el volumen de Docker `postgres_data`, por lo que tus tablas y registros no se perderán al apagar o reiniciar los contenedores. Si algún día deseas borrar la base de datos desde cero, usa `docker compose down -v`.
