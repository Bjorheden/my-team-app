// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ["dist/*"],
  },
  {
    // The `import/no-unresolved` rule doesn't understand TypeScript path aliases
    // (e.g. `@/lib/api`).  TypeScript itself — enforced by `tsc --noEmit` in CI —
    // is the authoritative resolver for these imports, so we disable the rule here.
    rules: {
      "import/no-unresolved": "off",
    },
  },
]);
