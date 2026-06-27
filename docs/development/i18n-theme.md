# I18n And Theme

The frontend is a Vue 3 application. Theme support and i18n are active in the
Vue shell and views.

## Locale Files

- English: `manager/frontend/src/locales/en.json`
- Simplified Chinese: `manager/frontend/src/locales/zh-CN.json`

When extending the locale set:

1. Add the key to `en.json`.
2. Add the same key to `zh-CN.json`.
3. Use `useI18n()` from Vue code instead of hard-coding user-facing text.
4. Run `node manager/frontend/tests/ui-foundation.test.mjs`.

The locale test asserts both files expose the same flattened key set.

The current rendering path uses the Vue i18n composable.

## Theme Modes

Theme modes are implemented in `manager/frontend/src/theme-core.mjs` and are
applied from `manager/frontend/src/App.vue`:

- `light`: always applies the light palette.
- `dark`: always applies the dark palette.
- `system`: resolves through `prefers-color-scheme`.

The selected mode is stored in browser localStorage. The resolved theme is
written to `document.documentElement.dataset.theme`, and CSS variables in
`manager/frontend/styles.css` provide the palette.

The initial inline script in `manager/frontend/index.html` applies the stored
theme before CSS loads so the first paint matches the saved preference.

## Defaults

WebUI preference defaults are stored in manager config:

```yaml
webui:
  default_language: en
  default_theme: system
```

Users can override these in the browser without changing the YAML file.

## Build Requirements

Vite and `@vitejs/plugin-vue` require Node `^20.19.0 || >=22.12.0`. Use the
repository Docker-based build command when the host Node version is older:

```powershell
docker run --rm -v ${PWD}:/work -w /work/manager/frontend node:22-alpine sh -lc "npm ci >/tmp/npm.log && npm run build"
```
