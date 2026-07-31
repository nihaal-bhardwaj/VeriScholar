# VeriScholar frontend

Next.js (App Router) + TypeScript + Tailwind CSS application for the VeriScholar research-integrity screening tool.

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
├── layout.tsx   root layout and metadata (title: VeriScholar)
└── page.tsx     home page
```

Created with `create-next-app` (Next.js 16, Tailwind CSS v4).
