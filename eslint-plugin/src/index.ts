// Rules are registered here automatically by generate-rules.sh + opencode.
// Do not edit manually — run generate-rules.sh to add new rules.

import type { TSESLint } from "@typescript-eslint/utils";

// rule-imports-start
// rule-imports-end

const rules: Record<string, TSESLint.RuleModule<string, unknown[]>> = {
  // rule-entries-start
  // rule-entries-end
};

const plugin = {
  meta: { name: "vibe-types", version: "0.1.0" },
  rules,
  configs: {} as Record<string, unknown>,
};

Object.assign(plugin.configs, {
  recommended: {
    plugins: { "vibe-types": plugin },
    rules: {
      // recommended-rules-start
      // recommended-rules-end
    },
  },
  strict: {
    plugins: { "vibe-types": plugin },
    rules: {
      // strict-rules-start
      // strict-rules-end
    },
  },
});

export default plugin;
