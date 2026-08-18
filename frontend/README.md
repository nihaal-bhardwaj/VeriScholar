# Mini Project frontend

Next.js (App Router) + TypeScript + Tailwind CSS application for the Mini Project research-integrity screening tool.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Validation

```bash
npm run lint
npm run build
```

## Current state

Minimal scaffold: home page with placeholder navigation (Paper Analyser, Review Detector, Methodology). No backend integration yet.

## Layout

```text
app/
├── layout.tsx   root layout and metadata (title: Mini Project)
└── page.tsx     home page
```

Created with `create-next-app` (Next.js 16, Tailwind CSS v4).

## Dependency overrides (temporary)

`package.json` declares `overrides` for `postcss` and `sharp`. This is temporary and exists because the pinned Next.js release (16.2.12) still depends on vulnerable transitive versions:

- `postcss` (exact `8.4.31`) — advisories GHSA-qx2v-qp2m-jg93, GHSA-6g55-p6wh-862q, GHSA-r28c-9q8g-f849
- `sharp` (optional `^0.34.5`) — advisory GHSA-f88m-g3jw-g9cj

The overrides force patched versions (`postcss >= 8.5.18`, `sharp >= 0.35.0`) and are API-compatible within the same major version. Once a stable Next.js release updates these pins, the `overrides` block should be removed and the lockfile regenerated.
