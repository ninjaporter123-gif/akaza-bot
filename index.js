require('dotenv').config();
const { Telegraf } = require('telegraf');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const ADMIN_ID = Number(process.env.ADMIN_ID);
if (!TOKEN || !Number.isSafeInteger(ADMIN_ID) || ADMIN_ID <= 0) {
  throw new Error('Set TELEGRAM_BOT_TOKEN and ADMIN_ID in your hosting environment variables.');
}

const bot = new Telegraf(TOKEN);
const UPLOADS = path.join(__dirname, 'user_scripts');
const LOGS = path.join(__dirname, 'logs');
fs.mkdirSync(UPLOADS, { recursive: true });
fs.mkdirSync(LOGS, { recursive: true });

let child = null;
let activeName = null;
let logStream = null;
let startedAt = null;

const isAdmin = ctx => Boolean(ctx.from && ctx.from.id === ADMIN_ID);
const isRunning = () => Boolean(child && child.exitCode === null && child.signalCode === null);
const validName = name => typeof name === 'string' && /^[a-zA-Z0-9_-][a-zA-Z0-9_.-]*\.js$/.test(name) && !name.includes('..');
const esc = value => String(value).replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[ch]);
const say = (ctx, text, extra = {}) => ctx.reply(text, { parse_mode: 'HTML', ...extra });

const menu = {
  reply_markup: {
    keyboard: [
      [{ text: '🚀  Upload Script' }, { text: '🗂  My Files' }],
      [{ text: '▶️  Launch' }, { text: '⏹  Stop' }, { text: '♻️  Restart' }],
      [{ text: '📡  System Status' }, { text: '📜  Live Logs' }],
      [{ text: '🧭  Help & Commands' }]
    ],
    resize_keyboard: true,
    is_persistent: true
  }
};

const panel = (title, body) => `<b>╭━━━ ◈ AKAZA CORE ◈ ━━━╮</b>\n<b>${title}</b>\n<blockquote>${body}</blockquote><i>ＮＥＸＴ－ＧＥＮ  ＪＳ  ＨＯＳＴＩＮＧ</i>`;

async function stopScript() {
  const current = child;
  if (current && current.exitCode === null && current.signalCode === null) {
    await new Promise(resolve => {
      const timer = setTimeout(() => {
        if (current.exitCode === null && current.signalCode === null) current.kill('SIGKILL');
        resolve();
      }, 4000);
      current.once('exit', () => { clearTimeout(timer); resolve(); });
      current.kill('SIGTERM');
    });
  }
  child = null;
  if (logStream) { logStream.end(); logStream = null; }
}

async function startScript(ctx, name) {
  if (!validName(name)) return say(ctx, panel('⚠️ INVALID FILE', 'Use a simple <code>.js</code> filename.'));
  const file = path.join(UPLOADS, name);
  if (!fs.existsSync(file)) return say(ctx, panel('📂 FILE NOT FOUND', 'Upload the script before launching it.'));
  if (isRunning()) return say(ctx, panel('⚠️ CORE BUSY', `Already running: <code>${esc(activeName)}</code>\nStop it before launching another script.`));

  const logPath = path.join(LOGS, `${path.parse(name).name}.log`);
  logStream = fs.createWriteStream(logPath, { flags: 'a' });
  // Do not pass the bot token or hosting environment secrets to user scripts.
  const env = {
    PATH: process.env.PATH || '',
    NODE_ENV: 'production',
    HOME: process.env.HOME || '/tmp',
    TMPDIR: process.env.TMPDIR || '/tmp'
  };
  const proc = spawn(process.execPath, [file], { cwd: UPLOADS, env, stdio: ['ignore', 'pipe', 'pipe'] });
  child = proc;
  activeName = name;
  startedAt = Date.now();
  proc.stdout.pipe(logStream, { end: false });
  proc.stderr.pipe(logStream, { end: false });
  proc.on('error', error => logStream?.write(`\nRunner error: ${error.message}\n`));
  proc.on('exit', (code, signal) => {
    logStream?.write(`\n[CORE EXIT] code=${code} signal=${signal}\n`);
    logStream?.end();
    logStream = null;
    if (child === proc) child = null;
  });
  return say(ctx, panel('🟢 SCRIPT ONLINE', `File: <code>${esc(name)}</code>\nProcess ID: <code>${proc.pid}</code>\nState: <b>RUNNING</b>`));
}

bot.start(async ctx => {
  if (!isAdmin(ctx)) return;
  await say(ctx, panel('WELCOME, OPERATOR', 'Your private JavaScript control deck is ready.\n\nUse the command console below to upload, launch, monitor and stop your own scripts.'), menu);
});

bot.hears(/^🚀\s+Upload Script$/, async ctx => {
  if (!isAdmin(ctx)) return;
  return say(ctx, panel('📤 UPLOAD CHANNEL', 'Send your <b>.js</b> file as a Telegram document.\nMaximum size: <code>1 MB</code>\n\nOnly upload code you wrote or fully trust.'));
});

bot.on('document', async ctx => {
  if (!isAdmin(ctx)) return;
  const doc = ctx.message.document;
  const name = path.basename(doc.file_name || '');
  if (!validName(name)) return say(ctx, panel('⛔ FILE REJECTED', 'Only simple JavaScript <code>.js</code> files are accepted.'));
  if (doc.file_size > 1024 * 1024) return say(ctx, panel('⛔ SIZE LIMIT', 'Maximum upload size is <code>1 MB</code>.'));
  try {
    const url = await ctx.telegram.getFileLink(doc.file_id);
    const response = await fetch(url.href);
    if (!response.ok) throw new Error(`Download failed (${response.status})`);
    const data = Buffer.from(await response.arrayBuffer());
    if (data.length > 1024 * 1024) throw new Error('File exceeds the 1 MB limit.');
    fs.writeFileSync(path.join(UPLOADS, name), data, { flag: 'w' });
    return say(ctx, panel('✅ UPLOAD COMPLETE', `File: <code>${esc(name)}</code>\nSize: <code>${data.length.toLocaleString()} bytes</code>\nStatus: <b>STORED</b>`));
  } catch (error) {
    return say(ctx, panel('⚠️ TRANSFER FAILED', esc(error.message)));
  }
});

bot.hears(/^🗂\s+My Files$/, ctx => {
  if (!isAdmin(ctx)) return;
  const files = fs.readdirSync(UPLOADS).filter(validName).sort();
  const body = files.length ? files.map((name, i) => `${i + 1}. <code>${esc(name)}</code>`).join('\n') : 'No scripts stored yet. Upload a <code>.js</code> file to begin.';
  return say(ctx, panel(`🗂 SCRIPT VAULT · ${files.length}`, body));
});

bot.hears(/^▶️\s+Launch$/, ctx => {
  if (!isAdmin(ctx)) return;
  const files = fs.readdirSync(UPLOADS).filter(validName);
  if (!files.length) return say(ctx, panel('📭 VAULT EMPTY', 'Upload a JavaScript file first.'));
  if (files.length > 1) return say(ctx, panel('SELECT A SCRIPT', `More than one file found. Use:\n<code>/run filename.js</code>`));
  return startScript(ctx, files[0]);
});

bot.command('run', ctx => {
  if (!isAdmin(ctx)) return;
  const name = (ctx.message.text || '').trim().split(/\s+/)[1];
  return name ? startScript(ctx, name) : say(ctx, panel('COMMAND GUIDE', 'Usage: <code>/run filename.js</code>'));
});

bot.hears(/^⏹\s+Stop$/, async ctx => {
  if (!isAdmin(ctx)) return;
  if (!isRunning()) return say(ctx, panel('ℹ️ CORE IDLE', 'No script is currently running.'));
  const oldName = activeName;
  await stopScript();
  return say(ctx, panel('⏹ PROCESS HALTED', `Script: <code>${esc(oldName)}</code>\nState: <b>STOPPED</b>`));
});

bot.hears(/^♻️\s+Restart$/, async ctx => {
  if (!isAdmin(ctx)) return;
  if (!activeName) return say(ctx, panel('ℹ️ NOTHING TO RESTART', 'Launch a script once before using restart.'));
  const name = activeName;
  await stopScript();
  return startScript(ctx, name);
});

bot.hears(/^📡\s+System Status$/, ctx => {
  if (!isAdmin(ctx)) return;
  const running = isRunning();
  const uptime = running && startedAt ? `${Math.floor((Date.now() - startedAt) / 1000)} sec` : '—';
  return say(ctx, panel('📡 SYSTEM DIAGNOSTICS', `Runner: ${running ? '<b>🟢 ONLINE</b>' : '<b>🔴 IDLE</b>'}\nActive file: <code>${running ? esc(activeName) : 'None'}</code>\nRuntime: <code>${uptime}</code>\nStorage: <b>READY</b>`));
});

bot.hears(/^📜\s+Live Logs$/, ctx => {
  if (!isAdmin(ctx)) return;
  if (!activeName) return say(ctx, panel('📜 LOG STREAM', 'No script has been selected yet.'));
  const logPath = path.join(LOGS, `${path.parse(activeName).name}.log`);
  if (!fs.existsSync(logPath)) return say(ctx, panel('📜 LOG STREAM', 'No log output available yet.'));
  const output = fs.readFileSync(logPath, 'utf8').slice(-2500);
  return say(ctx, `<b>╭━━ ◈ LIVE LOGS ◈ ━━╮</b>\n<pre>${esc(output || '(no output)')}</pre>`);
});

bot.hears(/^🧭\s+Help & Commands$/, ctx => {
  if (!isAdmin(ctx)) return;
  return say(ctx, panel('🧭 COMMAND CENTER', '<code>/start</code> — Open control deck\n<code>/run file.js</code> — Launch a file\n\nUpload a .js document, then use Launch. Status and Live Logs show runner information.'));
});

bot.catch(error => console.error('Telegram bot error:', error));
bot.launch().then(() => console.log('AKAZA CORE JS HOSTING BOT online.'));
process.once('SIGINT', async () => { await stopScript(); bot.stop('SIGINT'); });
process.once('SIGTERM', async () => { await stopScript(); bot.stop('SIGTERM'); });
