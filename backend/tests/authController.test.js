jest.mock('../src/models/User');

const bcrypt = require('bcrypt');
const User = require('../src/models/User');
const { register, login } = require('../src/controllers/authController');

function mockRes() {
  return {
    statusCode: 200,
    body: null,
    cookieCalls: [],
    status(code) { this.statusCode = code; return this; },
    json(payload) { this.body = payload; return this; },
    cookie(name, value, opts) { this.cookieCalls.push({ name, value, opts }); return this; },
  };
}

beforeAll(() => {
  process.env.JWT_SECRET = 'test_secret';
  process.env.JWT_EXPIRES_IN = '7d';
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('register', () => {
  test('refuse un mot de passe trop court', async () => {
    const req = { body: { email: 'a@b.com', password: 'short' } };
    const res = mockRes();

    await register(req, res);

    expect(res.statusCode).toBe(400);
  });

  test('refuse un email déjà utilisé (409)', async () => {
    User.findOne.mockResolvedValue({ _id: 'existing' });
    const req = { body: { email: 'a@b.com', password: 'password123' } };
    const res = mockRes();

    await register(req, res);

    expect(res.statusCode).toBe(409);
  });

  test('crée un utilisateur avec un mot de passe hashé et pose le cookie JWT', async () => {
    User.findOne.mockResolvedValue(null);
    User.create.mockImplementation(async (data) => ({ _id: 'newid123', ...data }));

    const req = { body: { email: 'new@example.com', password: 'password123' } };
    const res = mockRes();

    await register(req, res);

    expect(res.statusCode).toBe(201);
    expect(res.body.email).toBe('new@example.com');

    // Le mot de passe transmis à User.create ne doit JAMAIS être en clair
    const createArg = User.create.mock.calls[0][0];
    expect(createArg.passwordHash).not.toBe('password123');
    const isValidHash = await bcrypt.compare('password123', createArg.passwordHash);
    expect(isValidHash).toBe(true);

    // Le cookie JWT doit être HttpOnly
    expect(res.cookieCalls[0].name).toBe('token');
    expect(res.cookieCalls[0].opts.httpOnly).toBe(true);
  });
});

describe('login', () => {
  test('refuse un email inconnu (401, sans révéler la raison précise)', async () => {
    User.findOne.mockResolvedValue(null);
    const req = { body: { email: 'inconnu@example.com', password: 'password123' } };
    const res = mockRes();

    await login(req, res);

    expect(res.statusCode).toBe(401);
  });

  test('refuse un mauvais mot de passe (401)', async () => {
    const passwordHash = await bcrypt.hash('bonmotdepasse', 10);
    User.findOne.mockResolvedValue({ _id: '1', email: 'a@b.com', role: 'user', passwordHash });

    const req = { body: { email: 'a@b.com', password: 'mauvais' } };
    const res = mockRes();

    await login(req, res);

    expect(res.statusCode).toBe(401);
  });

  test('connecte un utilisateur avec les bons identifiants', async () => {
    const passwordHash = await bcrypt.hash('bonmotdepasse', 10);
    User.findOne.mockResolvedValue({ _id: '1', email: 'a@b.com', role: 'user', passwordHash });

    const req = { body: { email: 'a@b.com', password: 'bonmotdepasse' } };
    const res = mockRes();

    await login(req, res);

    expect(res.statusCode).toBe(200);
    expect(res.body.email).toBe('a@b.com');
    expect(res.cookieCalls[0].name).toBe('token');
  });
});
