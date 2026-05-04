import { createRule } from "../utils/rule-creator";
import type { TSESTree } from "@typescript-eslint/utils";

export default createRule({
  name: "no-duplicate-discriminant-values",
  meta: {
    type: "problem",
    docs: {
      description: "Flags union types where multiple members share the same literal value on a discriminant property",
    },
    messages: {
      duplicateDiscriminant:
        "Duplicate discriminant value(s) {{duplicates}} found in union type. Each member should have a unique discriminant value. [T01]",
    },
    schema: [],
    fixable: undefined,
  },
  defaultOptions: [],
  create(context) {
    function getLiteralValueFromAnnotation(
      annotation: TSESTree.TypeNode
    ): string | null {
      if (annotation.type === "TSLiteralType") {
        return getLiteralValue(annotation.literal);
      }
      if (
        annotation.type === "TSStringKeyword" ||
        annotation.type === "TSNumberKeyword" ||
        annotation.type === "TSBooleanKeyword"
      ) {
        return null;
      }
      return getLiteralValue(annotation as any);
    }

    function getLiteralValue(literal: TSESTree.Literal): string | null {
      if (literal.type === "Literal") {
        if (typeof literal.value === "string") return literal.value;
        if (typeof literal.value === "number") return String(literal.value);
        if (typeof literal.value === "boolean") return String(literal.value);
      }
      return null;
    }

    function processUnionType(node: TSESTree.TSUnionType) {
      const discriminantMap = new Map<string, { key: string; memberIndex: number }[]>();

      node.types.forEach((unionMember, memberIndex) => {
        if (unionMember.type !== "TSTypeLiteral") return;

        for (const member of unionMember.members) {
          if (member.type !== "TSPropertySignature") continue;
          if (!(member.key.type === "Identifier" || member.key.type === "Literal"))
            continue;

          const keyName =
            member.key.type === "Identifier"
              ? member.key.name
              : String(member.key.value);

          if (!member.typeAnnotation?.typeAnnotation) continue;

          const literalValue = getLiteralValueFromAnnotation(
            member.typeAnnotation.typeAnnotation
          );

          if (literalValue !== null) {
            const mapKey = `${keyName}:${literalValue}`;
            if (!discriminantMap.has(mapKey)) {
              discriminantMap.set(mapKey, []);
            }
            discriminantMap.get(mapKey)!.push({ key: keyName, memberIndex });
          }

          break;
        }
      });

      const duplicates = new Map<
        string,
        { value: string; memberIndices: number[] }
      >();

      for (const [mapKey, entries] of discriminantMap.entries()) {
        if (entries.length > 1) {
          const [key, value] = mapKey.split(":");
          if (!duplicates.has(key)) {
            duplicates.set(key, { value, memberIndices: [] });
          }
          entries.forEach((e) => {
            duplicates.get(key)!.memberIndices.push(e.memberIndex);
          });
        }
      }

      if (duplicates.size > 0) {
        const duplicateEntries = Array.from(duplicates.entries()).map(
          ([key, { memberIndices }]) =>
            `${key} (members: ${memberIndices.map((i) => i + 1).join(", ")})`
        );

        context.report({
          node,
          messageId: "duplicateDiscriminant",
          data: {
            duplicates: duplicateEntries.join("; "),
          },
        });
      }
    }

    return {
      TSUnionType: processUnionType,
    };
  },
});
