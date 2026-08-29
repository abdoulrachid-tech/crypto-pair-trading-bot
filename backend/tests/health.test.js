const request = require('supertest');

// Les modèles Mongoose ne sont importés qu'à l'intérieur des contrôleurs appelés
// par les routes protégées ; comme ce fichier ne teste que /api/health (sans DB),
// aucun mock n'est nécessaire ici.
const createApp = require('../app');

describe('GET /api/health', () => {
  const app = createApp();

  test('retourne un statut ok avec un timestamp', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.timestamp).toBeDefined();
  });
});

describe('Routes inconnues', () => {
  const app = createApp();

  test('retourne 404 pour une route non définie', async () => {
    const res = await request(app).get('/api/route-inexistante');
    expect(res.status).toBe(404);
  });
});

describe('Middleware CORS', () => {
  const app = createApp();

  test('autorise l\'origine configurée avec credentials', async () => {
    const res = await request(app)
      .get('/api/health')
      .set('Origin', process.env.FRONTEND_ORIGIN || 'http://localhost:5173');
    expect(res.headers['access-control-allow-credentials']).toBe('true');
  });
});
