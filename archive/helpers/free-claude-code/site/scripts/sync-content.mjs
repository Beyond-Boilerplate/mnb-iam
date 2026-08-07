#!/usr/bin/env node
/**
 * Sync lessons/*.md → Starlight content (markdown SoT stays in ../lessons).
 * Run from site/: node scripts/sync-content.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(__dirname, '..');
const lessonsRoot = path.resolve(siteRoot, '../lessons');
const modulesOut = path.join(siteRoot, 'src/content/docs/modules');
const templatesOut = path.join(siteRoot, 'public/templates');

const MODULES = [
  { dir: '01-slash-commands', title: '01 — Slash commands', order: 1 },
  { dir: '02-memory', title: '02 — Memory', order: 2 },
  { dir: '03-skills', title: '03 — Skills', order: 3 },
  { dir: '04-subagents', title: '04 — Subagents', order: 4 },
  { dir: '05-mcp', title: '05 — MCP', order: 5 },
  { dir: '06-hooks', title: '06 — Hooks', order: 6 },
  { dir: '07-plugins', title: '07 — Plugins', order: 7 },
  { dir: '08-checkpoints', title: '08 — Checkpoints', order: 8 },
  { dir: '09-advanced', title: '09 — Advanced', order: 9 },
  { dir: '10-cli', title: '10 — CLI', order: 10 },
  { dir: '11-ops-playbooks', title: '11 — Ops playbooks', order: 11 },
];

fs.mkdirSync(modulesOut, { recursive: true });
fs.mkdirSync(templatesOut, { recursive: true });

function stripFirstH1(md) {
  return md.replace(/^#\s+[^\n]+\n+/, '');
}

function rewriteTemplateLinks(md, moduleDir) {
  // Point relative template links at /templates/<module>/…
  return md.replace(
    /\]\((?!https?:|\/|#|\.\.\/)([^)]+)\)/g,
    (full, rel) => {
      if (rel.endsWith('.md') && !rel.includes('artifacts')) {
        // Keep in-page anchors; file links → public templates
        if (rel.startsWith('#')) return full;
        return `](/templates/${moduleDir}/${rel})`;
      }
      if (rel.match(/\.(sh|json|md)$/)) {
        return `](/templates/${moduleDir}/${rel})`;
      }
      return full;
    }
  );
}

for (const mod of MODULES) {
  const srcDir = path.join(lessonsRoot, mod.dir);
  const readme = path.join(srcDir, 'README.md');
  if (!fs.existsSync(readme)) {
    console.warn('skip missing', mod.dir);
    continue;
  }
  let body = fs.readFileSync(readme, 'utf8');
  body = stripFirstH1(body);
  body = rewriteTemplateLinks(body, mod.dir);

  const banner = `:::tip[Zero tokens]
This page is static. Read and do the labs in your editor/terminal — no Claude session required for learning.
:::

`;

  const page = `---
title: ${JSON.stringify(mod.title).slice(1, -1)}
description: Staff Claude Code module ${mod.order}
sidebar:
  order: ${mod.order}
---

${banner}${body}
`;

  fs.writeFileSync(path.join(modulesOut, `${mod.dir}.md`), page);

  // Copy module assets (templates, scripts) into public
  const dest = path.join(templatesOut, mod.dir);
  fs.mkdirSync(dest, { recursive: true });
  for (const ent of fs.readdirSync(srcDir, { withFileTypes: true })) {
    if (ent.name === 'README.md') continue;
    const from = path.join(srcDir, ent.name);
    const to = path.join(dest, ent.name);
    if (ent.isDirectory()) {
      fs.cpSync(from, to, { recursive: true });
    } else {
      fs.copyFileSync(from, to);
    }
  }
  console.log('synced', mod.dir);
}

// Sync top-level guides from lessons
const guideMap = [
  ['LEARNING-ROADMAP.md', 'guides/roadmap.md', 'Learning roadmap', 2],
  ['CATALOG.md', 'guides/catalog.md', 'Feature catalog', 3],
];

for (const [srcName, outRel, title, order] of guideMap) {
  const src = path.join(lessonsRoot, srcName);
  if (!fs.existsSync(src)) continue;
  let body = stripFirstH1(fs.readFileSync(src, 'utf8'));
  // Fix module links for site
  body = body.replace(/\]\((\d{2}-[^)]+)\/\)/g, '](/modules/$1/)');
  body = body.replace(/\]\((\d{2}-[^)]+)\/README\.md\)/g, '](/modules/$1/)');
  const page = `---
title: ${title}
sidebar:
  order: ${order}
---

${body}
`;
  const out = path.join(siteRoot, 'src/content/docs', outRel);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, page);
  console.log('synced', outRel);
}

console.log('done');
