import { ESLintUtils } from "@typescript-eslint/utils";

export const createRule = ESLintUtils.RuleCreator(
  (name) =>
    `https://github.com/jpablo/vibe-types/blob/main/eslint-plugin/docs/rules/${name}.md`,
);
