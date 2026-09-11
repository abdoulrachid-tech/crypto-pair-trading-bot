const { spawn, execSync } = require('child_process');

/**
 * Démarre/arrête le bot Python comme process natif local (pas de conteneur,
 * pas d'orchestrateur externe) — adapté à un déploiement où backend et bot
 * tournent sur la même machine avec des bases de données natives.
 *
 * Limitation connue : l'état "running" n'est fiable que tant que CE process
 * backend n'a pas redémarré depuis le dernier démarrage du bot (la référence
 * au process enfant est en mémoire, pas persistée). Si le backend redémarre
 * (ex. nodemon), il perd la référence même si le bot continue de tourner en
 * arrière-plan — dans ce cas, vérifiez le Gestionnaire des tâches Windows.
 */
let child = null;
let startedAt = null;

function getStatus() {
  return {
    running: !!child && child.exitCode === null,
    pid: child ? child.pid : null,
    startedAt,
  };
}

function start() {
  if (child && child.exitCode === null) {
    const err = new Error('Le bot tourne déjà (utilisez "Arrêter" avant de relancer).');
    err.status = 409;
    throw err;
  }

  const pythonExe = process.env.TRADING_BOT_PYTHON;
  const botDir = process.env.TRADING_BOT_DIR;
  if (!pythonExe || !botDir) {
    const err = new Error(
      'TRADING_BOT_PYTHON et TRADING_BOT_DIR doivent être définis dans backend/.env pour piloter le bot depuis l\'interface.'
    );
    err.status = 500;
    throw err;
  }

  child = spawn(pythonExe, ['-m', 'src.main'], {
    cwd: botDir,
    env: process.env,
    windowsHide: true,
  });
  startedAt = new Date().toISOString();

  child.stdout.on('data', (data) => {
    process.stdout.write(`[bot] ${data}`);
  });
  child.stderr.on('data', (data) => {
    process.stderr.write(`[bot:err] ${data}`);
  });
  child.on('exit', (code) => {
    console.log(`[bot] process terminé (code ${code}).`);
  });
  child.on('error', (err) => {
    console.error('[bot] impossible de démarrer le process :', err.message);
  });

  return getStatus();
}

async function stop() {
  if (!child || child.exitCode !== null) {
    return { running: false, pid: null, startedAt: null };
  }

  const pid = child.pid;
  child.kill(); // termine le process (SIGTERM sous Unix, arrêt direct sous Windows)

  // Laisse un court délai pour un arrêt propre, puis force si nécessaire.
  await new Promise((resolve) => setTimeout(resolve, 2000));

  if (child && child.exitCode === null) {
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /pid ${pid} /T /F`);
      } else {
        child.kill('SIGKILL');
      }
    } catch (e) {
      // Le process s'est déjà arrêté entre-temps — rien à faire.
    }
  }

  child = null;
  startedAt = null;
  return { running: false, pid: null, startedAt: null };
}

module.exports = { start, stop, getStatus };
