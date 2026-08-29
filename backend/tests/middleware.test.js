const jwt = require('jsonwebtoken');
const { requireAuth, requireAdmin } = require('../src/middleware/auth');
const { requireBotToken } = require('../src/middleware/botAuth');

function mockRes() {
  return {
    statusCode: null,
    body: null,
    status(code) { this.statusCode = code; return this; },
    json(payload) { this.body = payload; return this; },
  };
}

beforeAll(() => {
  process.env.JWT_SECRET = 'test_secret';
});

describe('requireAuth', () => {
  test('rejette une requête sans cookie token (401)', () => {
    const req = { cookies: {} };
    const res = mockRes();
    const next = jest.fn();

    requireAuth(req, res, next);

    expect(res.statusCode).toBe(401);
    expect(next).not.toHaveBeenCalled();
  });

  test('rejette un token invalide (401)', () => {
    const req = { cookies: { token: 'token.invalide.ici' } };
    const res = mockRes();
    const next = jest.fn();

    requireAuth(req, res, next);

    expect(res.statusCode).toBe(401);
    expect(next).not.toHaveBeenCalled();
  });

  test('accepte un token valide et attache req.user', () => {
    const token = jwt.sign({ id: 'abc123', email: 'a@b.com', role: 'user' }, process.env.JWT_SECRET);
    const req = { cookies: { token } };
    const res = mockRes();
    const next = jest.fn();

    requireAuth(req, res, next);

    expect(next).toHaveBeenCalled();
    expect(req.user.email).toBe('a@b.com');
  });
});

describe('requireAdmin', () => {
  test("refuse l'accès à un utilisateur non admin (403)", () => {
    const req = { user: { role: 'user' } };
    const res = mockRes();
    const next = jest.fn();

    requireAdmin(req, res, next);

    expect(res.statusCode).toBe(403);
    expect(next).not.toHaveBeenCalled();
  });

  test('autorise un utilisateur admin', () => {
    const req = { user: { role: 'admin' } };
    const res = mockRes();
    const next = jest.fn();

    requireAdmin(req, res, next);

    expect(next).toHaveBeenCalled();
  });
});

describe('requireBotToken', () => {
  const OLD_ENV = process.env.BOT_API_TOKEN;
  afterEach(() => { process.env.BOT_API_TOKEN = OLD_ENV; });

  test('rejette une requête sans le bon token (401)', () => {
    process.env.BOT_API_TOKEN = 'secret123';
    const req = { headers: { authorization: 'Bearer mauvais_token' } };
    const res = mockRes();
    const next = jest.fn();

    requireBotToken(req, res, next);

    expect(res.statusCode).toBe(401);
    expect(next).not.toHaveBeenCalled();
  });

  test('accepte le bon token', () => {
    process.env.BOT_API_TOKEN = 'secret123';
    const req = { headers: { authorization: 'Bearer secret123' } };
    const res = mockRes();
    const next = jest.fn();

    requireBotToken(req, res, next);

    expect(next).toHaveBeenCalled();
  });

  test("n'exige rien si BOT_API_TOKEN n'est pas configuré côté serveur", () => {
    delete process.env.BOT_API_TOKEN;
    const req = { headers: {} };
    const res = mockRes();
    const next = jest.fn();

    requireBotToken(req, res, next);

    expect(next).toHaveBeenCalled();
  });
});
