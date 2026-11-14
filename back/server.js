const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

const db = new sqlite3.Database('./fire_hunters.db', (err) => {
  if (err) console.error('Error SQLite:', err.message);
  else console.log('Base de datos SQLite conectada.');
});

app.get('/', (req, res) => {
  res.json({ message: 'Fire Hunters API (Backend) funcionando' });
});

app.listen(PORT, () => {
  console.log(`Servidor backend en http://localhost:${PORT}`);
});
