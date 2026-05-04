// Rules are registered here automatically by generate-rules.sh + opencode.
// Do not edit manually — run generate-rules.sh to add new rules.

import type { TSESLint } from "@typescript-eslint/utils";

// rule-imports-start
import noAsAnyInExhaustiveness from "./rules/no-as-any-in-exhaustiveness";
import noParallelBooleanFlags from "./rules/no-parallel-boolean-flags";
import noDuplicateDiscriminantValues from "./rules/no-duplicate-discriminant-values";
import noSilentFallbackInDefaultCase from "./rules/no-silent-fallback-in-default-case";
import requireExhaustivenessCheck from "./rules/require-exhaustiveness-check";
import noOptionalFieldsForMutuallyExclusiveShapes from "./rules/no-optional-fields-for-mutually-exclusive-shapes";
import noKitchenSinkVariants from "./rules/no-kitchen-sink-variants";
import noErrorCodeTupleReturn from "./rules/no-error-code-tuple-return";
import noWidenedDiscriminantAnnotation from "./rules/no-widened-discriminant-annotation";
// rule-imports-end

const rules: Record<string, TSESLint.RuleModule<string, unknown[]>> = {
  // rule-entries-start
  "no-as-any-in-exhaustiveness": noAsAnyInExhaustiveness,
  "no-parallel-boolean-flags": noParallelBooleanFlags,
  "no-duplicate-discriminant-values": noDuplicateDiscriminantValues,
  "no-silent-fallback-in-default-case": noSilentFallbackInDefaultCase,
  "require-exhaustiveness-check": requireExhaustivenessCheck,
  "no-optional-fields-for-mutually-exclusive-shapes": noOptionalFieldsForMutuallyExclusiveShapes,
  "no-kitchen-sink-variants": noKitchenSinkVariants,
  "no-error-code-tuple-return": noErrorCodeTupleReturn,
  "no-widened-discriminant-annotation": noWidenedDiscriminantAnnotation,
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
      "vibe-types/no-as-any-in-exhaustiveness": "warn",
      "vibe-types/no-parallel-boolean-flags": "warn",
      "vibe-types/no-duplicate-discriminant-values": "warn",
      "vibe-types/no-silent-fallback-in-default-case": "warn",
      "vibe-types/require-exhaustiveness-check": "warn",
      "vibe-types/no-optional-fields-for-mutually-exclusive-shapes": "warn",
      "vibe-types/no-kitchen-sink-variants": "warn",
      "vibe-types/no-error-code-tuple-return": "warn",
      "vibe-types/no-widened-discriminant-annotation": "warn",
      // recommended-rules-end
    },
  },
  strict: {
    plugins: { "vibe-types": plugin },
    rules: {
      // strict-rules-start
      "vibe-types/no-as-any-in-exhaustiveness": "warn",
      "vibe-types/no-parallel-boolean-flags": "warn",
      "vibe-types/no-duplicate-discriminant-values": "warn",
      "vibe-types/no-silent-fallback-in-default-case": "warn",
      "vibe-types/require-exhaustiveness-check": "warn",
      "vibe-types/no-optional-fields-for-mutually-exclusive-shapes": "warn",
      "vibe-types/no-kitchen-sink-variants": "warn",
      "vibe-types/no-error-code-tuple-return": "warn",
      "vibe-types/no-widened-discriminant-annotation": "warn",
      // strict-rules-end
    },
  },
});

export default plugin;
