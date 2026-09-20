// Deploys docs/ to the Netlify project, wherever it is run from.
//   node deploy.js            production deploy
//   node deploy.js --draft    preview deploy (a unique URL, production untouched)
//
// The bare CLI form (`netlify deploy --dir . --site <id>`) publishes whatever
// the shell's current directory is — so the directory comes from this file's
// location, never from the shell (same script as rawlens-site, 2026-09-20).
'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SITE_ID = '44cd6ddc-b9a2-4a2e-9c6e-42c94e4f7ac6'; // Netlify project "streams-kryl"
const dir = path.join(__dirname, 'docs');

// refuse anything that is not plainly this site
const expected = ['index.html', 'sites.json', 'favicon.png', 'fonts'];
const missing = expected.filter((file) => !fs.existsSync(path.join(dir, file)));
if (missing.length) {
  console.error(`Not deploying: ${dir} is missing ${missing.join(', ')}.`);
  process.exit(1);
}
const folders = fs.readdirSync(dir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
  .map((entry) => entry.name);
const unexpected = folders.filter((name) => name !== 'fonts');
if (unexpected.length) {
  console.error(`Not deploying: unexpected folders in docs/ (${unexpected.join(', ')}). ` +
    'Add the folder to deploy.js if it belongs.');
  process.exit(1);
}
try {
  const entries = JSON.parse(fs.readFileSync(path.join(dir, 'sites.json'), 'utf8'));
  if (!Array.isArray(entries) || !entries.length) throw new Error('expected a non-empty array');
} catch (err) {
  console.error(`Not deploying: docs/sites.json is not usable — ${err.message}`);
  process.exit(1);
}

const args = ['deploy', '--dir', dir, '--site', SITE_ID];
if (!process.argv.includes('--draft')) args.push('--prod');
console.log(`Deploying ${dir}\n> netlify ${args.join(' ')}`);
// cwd too: the CLI drops its .netlify/ state folder wherever it runs — keep it
// here, where it is gitignored, not in whatever project the shell was in
const result = spawnSync('netlify', args, { stdio: 'inherit', shell: true, cwd: __dirname });
process.exit(result.status === null ? 1 : result.status);
