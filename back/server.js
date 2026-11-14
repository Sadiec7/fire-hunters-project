const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Configuración del Pool de PostgreSQL
// Soporta URL directa (DATABASE_URL) o variables individuales
const pool = new Pool(
  process.env.DATABASE_URL
    ? { connectionString: process.env.DATABASE_URL }
    : {
        host: process.env.DB_HOST || 'postgres',
        port: process.env.DB_PORT ? parseInt(process.env.DB_PORT, 10) : 5432,
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'postgres',
        database: process.env.DB_NAME || 'fire_hunters_db',
      }
);

// Comprobar conexión inicial a PostgreSQL
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('❌ Error al conectar con PostgreSQL:', err.message);
  } else {
    console.log('✅ Base de datos PostgreSQL conectada exitosamente.');
  }
});

// Ruta principal
app.get('/', (req, res) => {
  res.json({ message: 'Fire Hunters API (Backend) funcionando' });
});

// Ruta para verificar el estado de la base de datos
app.get('/db-status', async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW() as current_time, current_database() as db_name');
    res.json({
      status: 'conectado',
      motor: 'PostgreSQL',
      base_de_datos: result.rows[0].db_name,
      hora_servidor: result.rows[0].current_time
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      mensaje: 'No se pudo conectar a la base de datos',
      error: error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor backend en http://localhost:${PORT}`);
});
