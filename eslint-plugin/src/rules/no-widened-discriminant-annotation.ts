import { createRule } from "../utils/rule-creator";

export default createRule({
  name: "no-widened-discriminant-annotation",
  meta: {
    type: "problem",
    docs: {
      description: "disallows object literals with discriminant fields without explicit type annotations, preventing literal type widening",
      requiresTypeChecking: true,
    },
    messages: {
      noAnnotation: "Object literal with discriminant field '{{fieldName}}' lacks explicit type annotation. The literal value may widen to '{{widenedType}}'. [T01]",
    },
    schema: [],
    fixable: undefined,
  },
  defaultOptions: [],
  create(context) {
    return {
      VariableDeclarator(node) {
        const { id, init } = node;

        if (init?.type !== "ObjectExpression") {
          return;
        }

        if (id.type !== "Identifier") {
          return;
        }

        const discriminantNames = ["kind", "type", "status"];
        const hasDiscriminant = init.properties.some((prop) => {
          if (prop.type !== "Property") {
            return false;
          }

          if (prop.key.type !== "Identifier") {
            return false;
          }

          const keyName = prop.key.name;

          if (!discriminantNames.includes(keyName)) {
            return false;
          }

          if (prop.value.type === "Literal" && typeof prop.value.value === "string") {
            return true;
          }

          return false;
        });

        if (!hasDiscriminant) {
          return;
        }

        const hasTypeAnnotation = id.typeAnnotation !== undefined;

        const hasAsConst = init.type === "TSAsExpression" && init.expression.type === "ObjectExpression" && init.typeAnnotation.type === "TSTypeAnnotation" && init.typeAnnotation.typeAnnotation.type === "TSLiteralType" && init.typeAnnotation.typeAnnotation.literal.type === "Identifier" && init.typeAnnotation.typeAnnotation.literal.name === "const";

        if (hasTypeAnnotation) {
          return;
        }

        if (hasAsConst) {
          return;
        }

        const discriminantProperty = init.properties.find((prop) => {
          if (prop.type !== "Property") {
            return false;
          }

          if (prop.key.type !== "Identifier") {
            return false;
          }

          if (!discriminantNames.includes(prop.key.name)) {
            return false;
          }

          if (prop.value.type === "Literal" && typeof prop.value.value === "string") {
            return true;
          }

          return false;
        });

        if (discriminantProperty && discriminantProperty.type === "Property" && discriminantProperty.key.type === "Identifier") {
          context.report({
            node,
            messageId: "noAnnotation",
            data: {
              fieldName: discriminantProperty.key.name,
              widenedType: "string",
            },
          });
        }
      },
    };
  },
});
