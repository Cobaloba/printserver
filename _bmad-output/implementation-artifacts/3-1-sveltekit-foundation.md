# Story 3.1: SvelteKit Foundation

Status: review

## Story

As a developer,
I want the SvelteKit frontend configured with Tailwind v4, PWA tooling, and the Vite API proxy,
So that the development environment matches production configuration exactly.

## Acceptance Criteria

1. **Given** `frontend/svelte.config.js` **When** reviewed **Then** `@sveltejs/adapter-static` is configured with `fallback: 'index.html'` and SSR is disabled

2. **Given** `frontend/vite.config.ts` **When** reviewed **Then** it includes `tailwindcss()` from `@tailwindcss/vite`, `sveltekit()`, `VitePWA({...})`, and a server proxy rule forwarding `/api` to `http://localhost:9000`

3. **Given** `frontend/src/app.css` **When** reviewed **Then** it contains `@import "tailwindcss";` and a `@theme {}` block defining at minimum dark background, card surface, and accent colour tokens

4. **Given** `cd frontend && npm run build` **When** executed **Then** `frontend/build/` is produced without errors and `frontend/build/index.html` exists

5. **Given** `cd frontend && npm run dev` **When** the dev server starts on port 5173 **Then** the page loads without console errors and requests to `/api/*` are proxied to port 9000

## Tasks / Subtasks

- [x] Task 1: Audit and confirm `svelte.config.js` (AC: 1)
  - [x] Verify `@sveltejs/adapter-static` with `fallback: 'index.html'`
  - [x] Verify `frontend/src/routes/+layout.ts` exports `export const ssr = false`

- [x] Task 2: Audit and confirm `vite.config.ts` (AC: 2)
  - [x] Verify `tailwindcss()`, `sveltekit()`, `VitePWA({ registerType: 'autoUpdate' })` plugins present
  - [x] Verify `/api` proxy rule points to `http://localhost:9000`

- [x] Task 3: Audit and confirm `app.css` (AC: 3)
  - [x] Verify `@import "tailwindcss"` present
  - [x] Verify `@theme {}` block has `--color-bg`, `--color-surface`, `--color-accent` tokens

- [x] Task 4: Run and verify build (AC: 4)
  - [x] Run `cd frontend && npm run build`
  - [x] Confirm `frontend/build/index.html` exists
  - [x] Fix any TypeScript or build errors found

- [x] Task 5: Run vitest to confirm test setup works
  - [x] Run `cd frontend && npm run test`
  - [x] Placeholder test at `src/lib/placeholder.test.ts` must pass

- [x] Task 6: Manual verification note (AC: 5)
  - [x] Document that dev server (`npm run dev`) must be started and `http://localhost:5173` confirmed console-error-free with `/api` proxy active

## Dev Notes

### Critical Context: Most Infrastructure Already Exists

Story 1.2 (Monorepo Scaffolding) already created and verified the frontend scaffold. This story's job is to **audit and confirm** those files meet Epic 3 requirements, run the build, and fix any gaps. Do NOT recreate files that already exist.

**Current file states (verified before story creation):**

| File | Status | Notes |
|------|--------|-------|
| `frontend/package.json` | ✅ Complete | All required deps present |
| `frontend/svelte.config.js` | ✅ Complete | adapter-static, fallback: 'index.html' |
| `frontend/vite.config.ts` | ✅ Complete | All 3 plugins + /api proxy |
| `frontend/src/app.css` | ✅ Complete | @import + @theme {} tokens |
| `frontend/src/routes/+layout.ts` | ✅ Complete | `export const ssr = false` |
| `frontend/build/index.html` | ✅ Exists | Previous build output |
| `frontend/src/routes/+layout.svelte` | Shell only | Full implementation in Story 3.4 |
| `frontend/src/routes/+page.svelte` | Shell only | Full implementation in Story 3.4 |
| `frontend/src/lib/` | placeholder.test.ts only | api.ts, stores.ts in Story 3.2; components in Story 3.3 |
| `frontend/static/` | Empty | manifest + icons in Story 3.9 |

### `ssr: false` Implementation Note

The AC says "adapter-static configured with `ssr: false`" — in SvelteKit, SSR is disabled per-layout via `export const ssr = false` in `+layout.ts`, NOT in `svelte.config.js`. The current `frontend/src/routes/+layout.ts` already exports this. This is the correct SvelteKit pattern. Do not attempt to add `ssr: false` to `svelte.config.js`.

### Current Config File Contents (exact)

**`frontend/svelte.config.js`:**
```js
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: 'index.html'
    })
  }
};
```

**`frontend/vite.config.ts`:**
```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit(),
    VitePWA({ registerType: 'autoUpdate' })
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:9000'
    }
  }
});
```

**`frontend/src/app.css`:**
```css
@import "tailwindcss";

@theme {
  --color-bg: #0f0f0f;
  --color-surface: #1a1a1a;
  --color-accent: #22c55e;
}
```

### VitePWA Scope

Story 3.1 uses minimal VitePWA config (`registerType: 'autoUpdate'` only). Full PWA configuration — `workbox.globPatterns`, manifest integration, `frontend/static/manifest.webmanifest`, icon files — is **Story 3.9**. Do NOT add workbox or manifest config here.

**Note from deferred-work.md:** "`ssr = false` + `vite-plugin-pwa` autoUpdate can serve stale shell after deploy — known PWA limitation; address in Story 3.9." This is a known accepted risk for now.

### Epic 2 Learnings (apply to all Epic 3 work)

From the Epic 2 retrospective:
- **Silent failures are the worst**: never use `except Exception: pass` or swallow errors; always surface them explicitly
- **Code review is mandatory**: schedule code review as a formal step after each story
- **Hardware demos for print pipeline stories**: this story does not touch print pipeline — no hardware demo required
- **Pi SSH**: username is `conor`, not `pi`; Pi IP is `192.168.0.25`

### Architecture Rules (mandatory for all Epic 3 stories)

From `architecture.md`:
- All JSON fields `snake_case` throughout — no camelCase in API payloads
- Frontend components: `PascalCase.svelte` (e.g. `StatusDot.svelte`)
- TypeScript utilities: `camelCase.ts` (e.g. `api.ts`, `stores.ts`)
- Route folders: `kebab-case` (e.g. `src/routes/free-text/`)
- TypeScript interfaces: `PascalCase` (e.g. `interface PrinterStatus {}`)
- Store names: `camelCase` (`printerStatus`, `rollState`)
- Never fetch API directly in components — always use `api.ts`
- Never create Svelte stores for per-form state — use local `let` variables
- `loading = false` always reset in `finally` block

### Package.json Dependency Placement (required)

```json
"devDependencies": {
  "vite-plugin-pwa": "^0.21.0"
},
"dependencies": {
  "@tailwindcss/vite": "^4.0.0",
  "svelte-sonner": "^0.3.0",
  "tailwindcss": "^4.0.0"
}
```
`svelte-sonner` is a runtime dep (renders in browser). `vite-plugin-pwa` is dev-only (build tool). Do not move them.

### Project Structure Notes

- `frontend/src/lib/` currently contains only `placeholder.test.ts` — this is intentional; `api.ts`, `stores.ts`, `polling.ts`, and `components/` are created in Stories 3.2–3.3
- `frontend/static/` is intentionally empty at this stage — PWA assets arrive in Story 3.9
- The current `+layout.svelte` shell and `+page.svelte` placeholder are intentional — don't flesh them out here (Story 3.4)
- `frontend/node_modules/` exists (deps were installed in Story 1.2)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.1 ACs]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend Architecture, Naming Patterns, Enforcement Guidelines]
- [Source: `_bmad-output/implementation-artifacts/1-2-monorepo-scaffolding.md` — what was scaffolded]
- [Source: `_bmad-output/implementation-artifacts/deferred-work.md` — PWA stale-shell deferred to Story 3.9]
- [Source: `_bmad-output/implementation-artifacts/epic-2-retro-2026-05-11.md` — Epic 2 learnings]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — all config files matched expected values on first audit; build and tests passed clean.

### Completion Notes List

- AC1 ✅: `svelte.config.js` uses `@sveltejs/adapter-static` with `fallback: 'index.html'`; `+layout.ts` exports `export const ssr = false` (correct SvelteKit pattern)
- AC2 ✅: `vite.config.ts` has `tailwindcss()`, `sveltekit()`, `VitePWA({ registerType: 'autoUpdate' })`, and `/api` proxy to `http://localhost:9000`
- AC3 ✅: `app.css` has `@import "tailwindcss"` and `@theme {}` with `--color-bg: #0f0f0f`, `--color-surface: #1a1a1a`, `--color-accent: #22c55e`
- AC4 ✅: `npm run build` completed without errors; `frontend/build/index.html` confirmed present; vite-plugin-pwa generated `sw.js` and `workbox-9c191d2f.js` (14 entries precached, 77 KiB)
- AC5 (manual): `vite.config.ts` proxy rule verified; dev server start requires manual confirmation in browser — run `cd frontend && npm run dev` and visit `http://localhost:5173`
- Vitest: 1/1 passing (`src/lib/placeholder.test.ts`)
- No code changes were needed — all files were correctly set up in Story 1.2

### File List

No files were modified — this story audited and verified the existing foundation from Story 1.2. All configs were already correct.
