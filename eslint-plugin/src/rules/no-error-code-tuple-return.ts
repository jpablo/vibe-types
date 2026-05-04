import { createRule } from "../utils/rule-creator";
import type { TSESTree } from "@typescript-eslint/utils";

export default createRule({
  name: "no-error-code-tuple-return",
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Disallow function returning tuple with error code flag in favor of Result ADT",
    },
    messages: {
      useResultADT:
        "Use a Result<T, E> ADT instead of returning a tuple with an error code",
    },
    schema: [],
  },
  defaultOptions: [],
  create(context) {
    function isNumberType(
      type: TSESTree.TypeNode,
    ): type is TSESTree.TSNumberKeyword {
      return type.type === "TSNumberKeyword";
    }

    function isNullabilityType(type: TSESTree.TypeNode): boolean {
      if (type.type === "TSNullKeyword") return true;
      if (type.type === "TSUndefinedKeyword") return true;
      if (type.type === "TSNumberKeyword") return true;
      if (type.type === "TSUnionType") {
        return type.types.some((t) =>
          t.type === "TSNullKeyword" ||
          t.type === "TSUndefinedKeyword" ||
          t.type === "TSNumberKeyword",
        );
      }
      return false;
    }

    function hasErrorTupleReturnType(
      returnType: TSESTree.TypeNode | undefined,
    ): boolean {
      if (!returnType || returnType.type !== "TSTupleType") return false;
      const tuple = returnType as TSESTree.TSTupleType;
      if (tuple.elementTypes.length !== 2) return false;
      const [first, second] = tuple.elementTypes;
      return isNumberType(first) && isNullabilityType(second);
    }

    function checkReturnStatements(
      body: TSESTree.BlockStatement | TSESTree.Expression,
    ): boolean {
      const statements: TSESTree.Statement[] = [];
      if (body.type === "BlockStatement") {
        statements.push(...body.body);
      }

      const returnStatements = statements.filter(
        (s): s is TSESTree.ReturnStatement => s.type === "ReturnStatement",
      );

      const hasErrorPattern = returnStatements.some((stmt) => {
        if (!stmt.argument || stmt.argument.type !== "ArrayExpression") {
          return false;
        }
        const elements = stmt.argument.elements;
        if (elements.length !== 2) return false;
        const [value, errorCode] = elements;
        if (!value) return false;
        if (errorCode?.type === "Literal" && typeof errorCode.value === "number") {
          return true;
        }
        if (errorCode?.type === "Identifier" && /^[eE]rror$/i.test(errorCode.name)) {
          return true;
        }
        if (errorCode?.type === "TSNullKeyword") {
          return true;
        }
        return false;
      });

      return hasErrorPattern;
    }

    const functionVisitor = (node:
      | TSESTree.FunctionDeclaration
      | TSESTree.FunctionExpression
      | TSESTree.ArrowFunctionExpression) => {
      if (
        node.returnType?.typeAnnotation &&
        hasErrorTupleReturnType(node.returnType.typeAnnotation)
      ) {
        context.report({
          node,
          messageId: "useResultADT",
        });
      }
    };

    return {
      FunctionDeclaration: functionVisitor,
      FunctionExpression: functionVisitor,
      ArrowFunctionExpression: functionVisitor,
    };
  },
});
