jest.mock('child_process', () => ({
  spawn: jest.fn(),
  execSync: jest.fn(),
}));

function makeFakeChild() {
  const listeners = {};
  return {
    pid: 1234,
    exitCode: null,
    stdout: { on: jest.fn() },
    stderr: { on: jest.fn() },
    on: jest.fn((event, cb) => { listeners[event] = cb; }),
    kill: jest.fn(),
    _listeners: listeners,
  };
}

describe('botProcess service', () => {
  let botProcess;
  let spawn;

  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    delete process.env.TRADING_BOT_DIR;
    delete process.env.TRADING_BOT_PYTHON;
    // Requis APRÈS resetModules() : chaque reset recrée une instance de mock
    // distincte pour 'child_process', c'est celle-ci que botProcess.js utilisera.
    ({ spawn } = require('child_process'));
    botProcess = require('../src/services/botProcess');
  });

  test('getStatus() indique "arrêté" avant tout démarrage', () => {
    expect(botProcess.getStatus()).toEqual({ running: false, pid: null, startedAt: null });
  });

  test('start() échoue explicitement si TRADING_BOT_DIR/PYTHON ne sont pas configurés', () => {
    expect(() => botProcess.start()).toThrow(/TRADING_BOT_PYTHON et TRADING_BOT_DIR/);
  });

  test('start() lance le bon exécutable avec le bon cwd quand la config est présente', () => {
    process.env.TRADING_BOT_DIR = '/fake/trading-bot';
    process.env.TRADING_BOT_PYTHON = '/fake/trading-bot/.venv/bin/python';
    spawn.mockReturnValue(makeFakeChild());

    const status = botProcess.start();

    expect(spawn).toHaveBeenCalledWith(
      '/fake/trading-bot/.venv/bin/python',
      ['-m', 'src.main'],
      expect.objectContaining({ cwd: '/fake/trading-bot' })
    );
    expect(status.running).toBe(true);
    expect(status.pid).toBe(1234);
  });

  test('start() refuse un second démarrage tant que le premier tourne (409)', () => {
    process.env.TRADING_BOT_DIR = '/fake/trading-bot';
    process.env.TRADING_BOT_PYTHON = '/fake/trading-bot/.venv/bin/python';
    spawn.mockReturnValue(makeFakeChild());

    botProcess.start();

    expect(() => botProcess.start()).toThrow(/tourne déjà/);
  });
});
