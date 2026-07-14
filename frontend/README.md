# Coral Matcher Frontend

Development and build instructions for the Coral Matcher interactive segmentation prototype.

## Local development

Install dependencies and start Vite dev server:

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## Build for production

```bash
cd frontend
npm install
npm run build
# preview build locally
npm run preview
```

## Type checking

```bash
cd frontend
npm run type-check
```

## Tests

No automated tests included yet. Manual smoke tests:

1. Start the dev server and open the page.
2. Upload an image and verify polygons render and selection works.
3. Click "Confirm Selection" to hit `/api/identify-coral` (backend must be running).
