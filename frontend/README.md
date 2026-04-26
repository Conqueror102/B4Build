# AI Build Advisor — frontend

Next.js 16 (App Router) + React 19 + Tailwind 4 + Clerk auth. Streams plan
generation from the FastAPI backend over Server-Sent Events.

## Run it

```bash
pnpm install        # only if node_modules is missing
cp .env.local.example .env.local
# fill NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY
pnpm dev            # http://localhost:3000
```

## Env vars

| Var | Required | What it does |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | no | Backend base URL. Defaults to `http://localhost:8000`. |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | yes | Clerk frontend key. |
| `CLERK_SECRET_KEY` | yes | Clerk backend key. Used by `middleware.ts`. |

## Folder layout

```
src/
  app/
    layout.tsx              # Geist + Geist_Mono, ClerkProvider, header/footer/Toaster
    page.tsx                # Homepage (hero, features, how it works, CTA)
    plan/new/page.tsx       # Idea intake form
    plan/[id]/page.tsx      # Streaming plan view (placeholder UI)
    sample/page.tsx
    about / pricing / how-it-works
    sign-in / sign-up
    globals.css             # design tokens + utility classes
  middleware.ts             # Clerk route protection
  components/
    ui/                     # primitives — all native, no Radix
      button, card, input, textarea, label, badge, separator,
      skeleton, tabs, dialog, tooltip, toast
    brand/                  # opinionated, brand-specific composites
      logo, gradient-heading, phase-card, metric-chip,
      empty-state, grid-bg
    layout/
      site-header, site-footer
  lib/
    utils.ts                # cn() — clsx + tailwind-merge
    types.ts                # mirror of backend Pydantic schemas
    api.ts                  # apiFetch + streamChat
    sse.ts                  # SSE -> AsyncGenerator<SseEvent>
```

## Design tokens

All colours live in `src/app/globals.css` as CSS variables (OKLCH):

- `--background` near-black, `--foreground` near-white
- `--card`, `--muted`, `--border` — three subtle dark surfaces
- `--accent-from` violet `oklch(0.7 0.2 295)` → `--accent-to` fuchsia `oklch(0.7 0.25 340)`
- `--ring` matches the violet for focus states
- Fonts: `--font-sans` = Geist, `--font-mono` = Geist Mono

Useful utility classes (defined under `@layer utilities`):

- `.gradient-text` — gradient-clipped text
- `.gradient-bg` — solid gradient fill
- `.gradient-border` — 1px gradient hairline border via mask
- `.glow` / `.glow-hover` — violet drop-shadow
- `.grid-bg` — radial-dot grid for hero backgrounds
- `.noise::after` — subtle SVG grain overlay
- `.animate-in-up` / `.animate-in-fade` — entrance animations

## Adding a page

1. Create the route under `src/app/<route>/page.tsx`.
2. If it should be public (no Clerk auth wall), add the matcher to
   `src/middleware.ts` → `isPublicRoute`.
3. Use the layout pattern:
   ```tsx
   <section className="mx-auto max-w-3xl px-4 py-24 sm:px-6">
     <Badge mono variant="outline">Section label</Badge>
     <GradientHeading as="h1" className="mt-4">Title</GradientHeading>
     <p className="mt-6 text-muted-foreground leading-relaxed">…</p>
   </section>
   ```

## Why no Radix

Two prior installer runs hung on `@radix-ui/react-*` over pnpm + Windows.
Every primitive in `components/ui/` is built from plain React + Tailwind 4 +
ARIA. Same UX, no install pain. If you ever need to swap to Radix later,
the public APIs are intentionally Radix-shaped.

## Build / lint

```bash
pnpm build
pnpm lint
```
