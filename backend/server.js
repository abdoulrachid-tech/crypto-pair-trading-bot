require('dotenv').config();

const createApp = require('./app');
const connectDB = require('./src/config/db');

const PORT = process.env.PORT || 5000;

async function start() {
  try {
    await connectDB();
    const app = createApp();
    app.listen(PORT, () => {
      console.log(`[API] Serveur démarré sur http://localhost:${PORT}`);
    });
  } catch (err) {
    console.error('Échec du démarrage du serveur :', err.message);
    process.exit(1);
  }
}

start();
