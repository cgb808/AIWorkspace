#!/usr/bin/env node
/**
 * memory-restore.mjs
 *
 * Restore a previously saved knowledge-graph snapshot (run-YYYY...) to the
 * active working set (root knowledge-graph directory) OR update only the
 * `latest` reference.
 *
 * Strategy: Copies snapshot contents back into graph root (excluding other
 * run-* dirs) unless --latest-only is provided (just repoints the symlink / pointer).
 *
 * Flags:
 *   --run <run-id>            (required) e.g. run-20250819-220821
 *   --graph-root <path>       (override discovery)
 *   --latest-only             (only update 'latest' reference)
 *   --clean-root              (remove existing top-level artifacts before copy)
 *   --dry-run                 (show actions without performing them)
 */
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(__dirname, '..');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { run: null, graphRoot: null, latestOnly: false, cleanRoot: false, dryRun: false };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--run') out.run = args[++i];
    else if (a === '--graph-root') out.graphRoot = args[++i];
    else if (a === '--latest-only') out.latestOnly = true;
    else if (a === '--clean-root') out.cleanRoot = true;
    else if (a === '--dry-run') out.dryRun = true;
  }
  if (!out.run) throw new Error('Missing --run <run-id>');
  return out;
}

async function pathExists(p) { try { await fs.access(p); return true; } catch { return false; } }

async function resolveGraphRoot(explicit) {
  if (explicit) return explicit;
  const candidates = [
    process.env.KNOWLEDGE_GRAPH_ROOT,
    path.join(repoRoot, '..', 'Artifact', 'knowledge-graph'),
    path.join(repoRoot, 'knowledge-graph')
  ].filter(Boolean);
  for (const c of candidates) if (await pathExists(c)) return c;
  throw new Error('Could not locate knowledge-graph root');
}

async function listTopArtifacts(root) {
  const entries = await fs.readdir(root);
  return entries.filter(e => !/^run-/.test(e) && e !== 'latest');
}

async function removeArtifacts(root, files) {
  for (const f of files) {
    try { await fs.rm(path.join(root, f), { recursive: true, force: true }); } catch {/* ignore */}
  }
}

async function updateLatest(latestPath, target) {
  try { await fs.rm(latestPath, { recursive: true, force: true }); } catch {}
  try { await fs.symlink(target, latestPath); }
  catch { await fs.writeFile(latestPath, target + '\n'); }
}

async function main() {
  const args = parseArgs();
  const graphRoot = await resolveGraphRoot(args.graphRoot);
  const runDir = path.join(graphRoot, args.run);
  if (!(await pathExists(runDir))) throw new Error(`Run directory not found: ${runDir}`);
  const latestLink = path.join(graphRoot, 'latest');

  if (args.latestOnly) {
    if (!args.dryRun) await updateLatest(latestLink, runDir);
    console.log(`[memory-restore] latest -> ${runDir}${args.dryRun ? ' (dry-run)' : ''}`);
    return;
  }

  const artifacts = await listTopArtifacts(graphRoot);
  if (args.cleanRoot) {
    console.log('[memory-restore] Cleaning root artifacts:', artifacts.join(', '));
    if (!args.dryRun) await removeArtifacts(graphRoot, artifacts);
  }

  // Copy contents from run dir (excluding nested run-* directories just in case)
  const runEntries = await fs.readdir(runDir);
  for (const entry of runEntries) {
    if (/^run-/.test(entry)) continue;
    const src = path.join(runDir, entry);
    const dest = path.join(graphRoot, entry);
    const stat = await fs.stat(src);
    console.log(`[memory-restore] Copy ${entry}`);
    if (!args.dryRun) {
      if (stat.isDirectory()) {
        await fs.rm(dest, { recursive: true, force: true }).catch(()=>{});
        await fs.cp(src, dest, { recursive: true });
      } else {
        await fs.copyFile(src, dest);
      }
    }
  }

  if (!args.dryRun) await updateLatest(latestLink, runDir);
  console.log(`[memory-restore] Restored ${args.run} into ${graphRoot}${args.dryRun ? ' (dry-run)' : ''}`);
}

main().catch(e => { console.error('[memory-restore] ERROR', e); process.exit(1); });
