# ZeroClaw Manager

This directory contains the WebUI manager skeleton. The current stage provides:

- a tiny Python backend with `/healthz` and `/api/status`;
- a static frontend placeholder served by the backend;
- a Dockerfile for the `manager` Compose service.
- frontend foundations for locale loading, browser preference persistence, and
  light/dark/system theme application.

Later stages will add configuration validation, Docker API integration, agent
container lifecycle operations, and generated ZeroClaw config rendering.

The manager is intended to be reached only through the host loopback binding in
`docker-compose.yml`.

## Frontend Foundation

The current frontend intentionally remains a static, framework-free browser
module app served by the Python manager. This keeps the phase-01 skeleton free
of a build step while still giving later phases shared utilities for UI text,
preferences, and theme state.

Internationalization uses structured JSON locale files under
`frontend/src/locales/`. English (`en`) is the default locale and Simplified
Chinese (`zh-CN`) is supported. All new user-facing WebUI text must use an i18n
key path, except literal technical values such as file names, protocols, model
IDs, provider IDs, and container names.

Theme support is implemented through CSS custom properties and the
`data-theme-mode` / `data-theme` attributes on `<html>`. Supported modes are
`light`, `dark`, and `system`; changing modes applies immediately without a page
reload. Browser-level language and theme preferences are persisted in
`localStorage`.

The backend exposes `/api/webui/defaults` so later configuration work can wire
manager defaults into the browser. Phase 02 should represent those defaults in
`config/manager.yaml` as:

```yaml
webui:
  default_language: en
  default_theme: system
```

For now the endpoint reads `WEBUI_DEFAULT_LANGUAGE` and `WEBUI_DEFAULT_THEME`,
falling back to `en` and `system`.

Run the frontend foundation checks with:

```sh
node manager/frontend/tests/ui-foundation.test.mjs
```
