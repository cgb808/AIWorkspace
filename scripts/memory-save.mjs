#!/usr/bin/env node
/**
 * memory-save.mjs
 *
 * Create a timestamped immutable snapshot (run-YYYYMMDD-HHMMSS) of the current
 * knowledge-graph artifact set and update the `latest` pointer (symlink or
 * pointer file).
 *
 * Sources searched (first existing wins unless --graph-root provided):
 *   1. $KNOWLEDGE_GRAPH_ROOT
 *   2. ../Artifact/knowledge-graph
 *   3. ./knowledge-graph (inside repo)
 *
 * Files copied (if present):
 *   - entities.json
 *   - relations.json
 *   - memory_snapshot*.json
 *   - COMPREHENSIVE_SYSTEM_CAPTURE.md
 *   - memory_graph.mmd
 *   - graph.json / manifest.json (prior run formats)
 *   - any additional *.md matched by --include-md-glob
 *
 * Outputs:
 *   knowledge-graph/run-<timestamp>/... + manifest.json
 *   knowledge-graph/latest  (symlink or pointer file) updated atomically.
 *
 * Usage examples:
 *   node scripts/memory-save.mjs
 *   node scripts/memory-save.mjs --dry-run
 *   node scripts/memory-save.mjs --graph-root ../Artifact/knowledge-graph --note "post-ingest"
 */
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';
import { execSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(__dirname, '..');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { dryRun: false, graphRoot: null, note: '', includeMdGlob: '' };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--dry-run') out.dryRun = true;
    else if (a === '--graph-root') out.graphRoot = args[++i];
    else if (a === '--note') out.note = args[++i];
    else if (a === '--include-md-glob') out.includeMdGlob = args[++i];
  }
  return out;
}

async function pathExists(p) {
  try { await fs.access(p); return true; } catch { return false; }
}

async function resolveGraphRoot(explicit) {
  if (explicit) return explicit;
  const candidates = [
    process.env.KNOWLEDGE_GRAPH_ROOT,
    path.join(repoRoot, '..', 'Artifact', 'knowledge-graph'),
    path.join(repoRoot, 'knowledge-graph')
  ].filter(Boolean);
  for (const c of candidates) {
    if (await pathExists(c)) return c;
  }
  // fallback create inside repo
  const fallback = path.join(repoRoot, 'knowledge-graph');
  await fs.mkdir(fallback, { recursive: true });
  return fallback;
}

function nowStamp() {
  const d = new Date();
  const pad = (n) => n.toString().padStart(2, '0');
  return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

async function globMd(base, pattern) {
  if (!pattern) return [];
  // minimal glob: only supports single '*' wildcard
  const rx = new RegExp('^' + pattern.split('*').map(s => s.replace(/[-/\\^$+?.()|[\]{}]/g, '\\$&')).join('.*') + '$');
  const entries = await fs.readdir(base);
  return entries.filter(e => rx.test(e));
}

async function sha256(p) {
  const data = await fs.readFile(p);
  return crypto.createHash('sha256').update(data).digest('hex');
}

async function main() {
  const args = parseArgs();
  const graphRoot = await resolveGraphRoot(args.graphRoot);
  const stamp = nowStamp();
  const runDir = path.join(graphRoot, `run-${stamp}`);
  const latestLink = path.join(graphRoot, 'latest');
  const candidateFiles = [
    'entities.json',
    'relations.json',
    'memory_graph.mmd',
    'graph.json',
    'manifest.json',
    'COMPREHENSIVE_SYSTEM_CAPTURE.md'
  ];
  // add memory_snapshot*.json
  const rootEntries = (await fs.readdir(graphRoot).catch(() => []));
  for (const f of rootEntries) {
    if (/^memory_snapshot.*\.json$/i.test(f)) candidateFiles.push(f);
  }
  // include extra md glob matches
  if (args.includeMdGlob) {
    const extras = await globMd(graphRoot, args.includeMdGlob);
    for (const e of extras) if (!candidateFiles.includes(e)) candidateFiles.push(e);
  }

  const existing = [];
  for (const f of candidateFiles) {
    const full = path.join(graphRoot, f);
    if (await pathExists(full)) existing.push(f);
  }

  if (!existing.length) {
    console.error('[memory-save] No knowledge-graph artifacts found to snapshot in', graphRoot);
    process.exit(2);
  }

  if (!args.dryRun) await fs.mkdir(runDir, { recursive: true });

  const manifest = {
    run: `run-${stamp}`,
    timestamp: new Date().toISOString(),
    note: args.note,
    sourceRoot: graphRoot,
    files: [],
    git: null
  };
  try {
    const rev = execSync('git rev-parse HEAD', { cwd: repoRoot, stdio: ['ignore','pipe','ignore'] }).toString().trim();
    manifest.git = { commit: rev };
  } catch { /* ignore */ }

  for (const f of existing) {
    const src = path.join(graphRoot, f);
    const dest = path.join(runDir, f);
    let size = 0; let hash = null;
    if (!args.dryRun) {
      await fs.copyFile(src, dest);
      const st = await fs.stat(dest);
      size = st.size;
      hash = await sha256(dest);
    } else {
      const st = await fs.stat(src);
      size = st.size;
      hash = await sha256(src);
    }
    manifest.files.push({ name: f, size, sha256: hash });
  }

  // write manifest
  if (!args.dryRun) {
    await fs.writeFile(path.join(runDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
    // update latest pointer atomically
    try {
      await fs.rm(latestLink, { force: true, recursive: true });
      await fs.symlink(runDir, latestLink);
    } catch {
      // fallback to pointer file
      await fs.writeFile(latestLink, runDir + '\n');
    }
  }

  console.log(`[memory-save] Snapshot ${manifest.run}${args.dryRun ? ' (dry-run)' : ''}`);
  console.log('[memory-save] Files:', manifest.files.map(f => f.name).join(', '));
  console.log('[memory-save] Location:', runDir);
}

main().catch(e => { console.error('[memory-save] ERROR', e); process.exit(1); });
