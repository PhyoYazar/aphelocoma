# Framework Discovery Patterns

When exploring a codebase for UX review, detect the framework first (check for `package.json`, `requirements.txt`, `Gemfile`, `Cargo.toml`, `pubspec.yaml`, or similar), then use matching patterns below.

## Django / Python Web

- Templates: `**/templates/**/*.html`
- Views: `**/views.py`, `**/views/**/*.py`
- URLs: `**/urls.py`
- Static assets: `**/static/**/*.{css,js}`
- Models: `**/models.py`, `**/models/**/*.py`
- Forms: `**/forms.py`
- Middleware: `**/middleware.py`
- Settings: `**/settings*.py`

## React / Next.js

- Components: `src/components/**/*.{jsx,tsx}`, `components/**/*.{jsx,tsx}`
- Pages/routes: `src/pages/**/*`, `app/**/{page,layout,loading,error}.{jsx,tsx}`
- API routes: `src/pages/api/**/*`, `app/api/**/route.{js,ts}`
- Styles: `**/*.{css,scss,module.css}`, `tailwind.config.*`
- State management: `**/store/**/*`, `**/context/**/*`, `**/hooks/**/*`
- Navigation: React Router setup, Next.js middleware, layout files

## Vue / Nuxt

- Components: `src/components/**/*.vue`, `components/**/*.vue`
- Pages: `src/views/**/*.vue`, `pages/**/*.vue`
- Router: `src/router/**/*`, `router/**/*`
- Stores: `src/stores/**/*`, `src/store/**/*`
- Layouts: `layouts/**/*.vue`
- Styles: `**/*.{css,scss}`, `assets/css/**/*`

## Svelte / SvelteKit

- Components: `src/lib/**/*.svelte`, `src/components/**/*.svelte`
- Routes: `src/routes/**/*.svelte`, `src/routes/**/+page.svelte`
- Layouts: `src/routes/**/+layout.svelte`
- Styles: `**/*.css`, `src/app.css`

## Rails

- Views: `app/views/**/*.{erb,haml,slim}`
- Controllers: `app/controllers/**/*.rb`
- Routes: `config/routes.rb`
- Assets: `app/assets/**/*`, `app/javascript/**/*`
- Models: `app/models/**/*.rb`
- Helpers: `app/helpers/**/*.rb`
- Layouts: `app/views/layouts/**/*`

## Laravel / PHP

- Views: `resources/views/**/*.blade.php`
- Controllers: `app/Http/Controllers/**/*.php`
- Routes: `routes/web.php`, `routes/api.php`
- Assets: `resources/css/**/*`, `resources/js/**/*`
- Models: `app/Models/**/*.php`
- Middleware: `app/Http/Middleware/**/*.php`

## Flutter / Mobile

- Screens: `lib/screens/**/*.dart`, `lib/pages/**/*.dart`
- Widgets: `lib/widgets/**/*.dart`
- Routes: `MaterialApp` router config, `go_router` setup
- State: `lib/providers/**/*`, `lib/bloc/**/*`, `lib/cubit/**/*`
- Theme: `ThemeData` definitions

## Angular

- Components: `src/app/**/*.component.{ts,html,css}`
- Routes: `src/app/**/*-routing.module.ts`, `src/app/app.routes.ts`
- Services: `src/app/**/*.service.ts`
- Templates: `src/app/**/*.component.html`
- Styles: `src/app/**/*.component.{css,scss}`, `src/styles.{css,scss}`

## General (framework-agnostic)

If you can't identify the framework:

1. **Entry point**: `index.html`, `main.*`, `app.*`, `server.*`
2. **Layout/shell**: outermost template wrapping all pages
3. **Route config**: URL patterns, path definitions, route maps
4. **Auth/middleware**: login, permission, role-related code
5. **CSS/design tokens**: CSS custom properties, theme files, design system
6. **Form handling**: `<form`, `onSubmit`, POST handlers
7. **AJAX/fetch calls**: `fetch(`, `axios`, `XMLHttpRequest`, WebSocket

## What to Ask the Explore Agent

When dispatching for UX review, include these instructions:

> Read the FULL content of every template/component file — not just file names.
> Read all view/controller files that serve these templates.
> Read the route/URL configuration completely.
> Read the base layout/shell and all CSS/style files.
> Read any client-side JavaScript/TypeScript that handles user interactions.
> Read data model definitions to understand the shapes behind the screens.
> For each screen, identify: URL, role access, available actions, navigation targets.
> Map which templates are served by which views at which URLs.
> Identify role-based differences in what different users see.
> Note the design system: colors, typography, spacing, component patterns.
