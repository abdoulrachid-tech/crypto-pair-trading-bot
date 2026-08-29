jest.mock('../src/models/Trade');
jest.mock('../src/models/BotLog');
jest.mock('../src/models/BotStatus');

const Trade = require('../src/models/Trade');
const BotLog = require('../src/models/BotLog');
const BotStatus = require('../src/models/BotStatus');
const {
  createTrade, listTrades, createLog, updateStatus, getPerformance,
} = require('../src/controllers/botController');

function mockRes() {
  return {
    statusCode: 200,
    body: null,
    status(code) { this.statusCode = code; return this; },
    json(payload) { this.body = payload; return this; },
  };
}

afterEach(() => jest.clearAllMocks());

describe('createTrade', () => {
  test('refuse une requête avec des champs manquants (400)', async () => {
    const req = { body: { symbolA: 'BTC/USDT' } };
    const res = mockRes();

    await createTrade(req, res);

    expect(res.statusCode).toBe(400);
  });

  test('crée un trade avec les champs fournis', async () => {
    Trade.create.mockResolvedValue({ id: 't1', symbolA: 'BTC/USDT', symbolB: 'ETH/USDT' });
    const req = {
      body: {
        symbolA: 'BTC/USDT', symbolB: 'ETH/USDT', signal: 'close',
        priceA: 65000, priceB: 3400, zscore: 0.3, pnl: 12.5,
      },
    };
    const res = mockRes();

    await createTrade(req, res);

    expect(res.statusCode).toBe(201);
    expect(Trade.create).toHaveBeenCalledTimes(1);
  });
});

describe('listTrades', () => {
  test('applique une limite plafonnée à 2000', async () => {
    const sortMock = jest.fn().mockReturnValue({ limit: jest.fn().mockResolvedValue([]) });
    Trade.find.mockReturnValue({ sort: sortMock });

    const req = { query: { limit: '999999' } };
    const res = mockRes();

    await listTrades(req, res);

    const limitFn = sortMock.mock.results[0].value.limit;
    expect(limitFn).toHaveBeenCalledWith(2000);
  });
});

describe('createLog', () => {
  test('refuse un log sans message (400)', async () => {
    const req = { body: {} };
    const res = mockRes();

    await createLog(req, res);

    expect(res.statusCode).toBe(400);
  });

  test('crée un log avec le niveau par défaut "info"', async () => {
    BotLog.create.mockResolvedValue({ id: 'l1', level: 'info', message: 'test' });
    const req = { body: { message: 'test' } };
    const res = mockRes();

    await createLog(req, res);

    expect(res.statusCode).toBe(201);
    expect(BotLog.create).toHaveBeenCalledWith({ level: 'info', message: 'test', meta: {} });
  });
});

describe('updateStatus', () => {
  test('fait un upsert sur botId="default" si non précisé', async () => {
    BotStatus.findOneAndUpdate.mockResolvedValue({ botId: 'default', isRunning: true });
    const req = { body: { isRunning: true } };
    const res = mockRes();

    await updateStatus(req, res);

    expect(BotStatus.findOneAndUpdate).toHaveBeenCalledWith(
      { botId: 'default' },
      { $set: { isRunning: true } },
      { new: true, upsert: true }
    );
  });
});

describe('getPerformance', () => {
  test('calcule correctement le PnL cumulé, le win rate et le max drawdown', async () => {
    const trades = [
      { pnl: 10, executedAt: new Date('2024-01-01') },
      { pnl: -5, executedAt: new Date('2024-01-02') },
      { pnl: 20, executedAt: new Date('2024-01-03') },
      { pnl: -30, executedAt: new Date('2024-01-04') },
    ];
    Trade.find.mockReturnValue({ sort: jest.fn().mockResolvedValue(trades) });

    const req = {};
    const res = mockRes();

    await getPerformance(req, res);

    expect(res.statusCode).toBe(200);
    expect(res.body.nTrades).toBe(4);
    expect(res.body.cumulativePnl).toBeCloseTo(-5); // 10 - 5 + 20 - 30 = -5
    expect(res.body.winRate).toBeCloseTo(2 / 4); // 2 trades positifs sur 4
    expect(res.body.maxDrawdown).toBeLessThan(0);
  });

  test("gère le cas où il n'y a aucun trade clôturé", async () => {
    Trade.find.mockReturnValue({ sort: jest.fn().mockResolvedValue([]) });
    const req = {};
    const res = mockRes();

    await getPerformance(req, res);

    expect(res.statusCode).toBe(200);
    expect(res.body.nTrades).toBe(0);
    expect(res.body.winRate).toBe(0);
  });
});
