// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  // Set `site` + `base` when deploying (e.g. GitHub Pages project site).
  // Local default: root.
  site: process.env.SITE_URL || undefined,
  base: process.env.SITE_BASE || '/',
  integrations: [
    starlight({
      title: 'Staff Claude Code',
      description:
        'A free, static staff-engineer guide to Claude Code — skills, hooks, agents, MCP, and ops playbooks.',
      favicon: '/favicon.svg',
      social: [],
      customCss: ['./src/styles/custom.css'],
      sidebar: [
        {
          label: 'Start here',
          items: [
            { label: 'Overview', slug: 'index' },
            { label: 'Get started', slug: 'guides/get-started' },
            { label: 'Learning roadmap', slug: 'guides/roadmap' },
            { label: 'Progress board', link: '/progress/' },
            { label: 'Feature catalog', slug: 'guides/catalog' },
          ],
        },
        {
          label: 'Modules',
          items: [{ autogenerate: { directory: 'modules' } }],
        },
      ],
      head: [
        {
          tag: 'link',
          attrs: {
            rel: 'preconnect',
            href: 'https://fonts.googleapis.com',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'preconnect',
            href: 'https://fonts.gstatic.com',
            crossorigin: 'anonymous',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'stylesheet',
            href: 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Outfit:wght@400;500;600;700&display=swap',
          },
        },
      ],
    }),
  ],
});
