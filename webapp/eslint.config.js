import tseslint from "typescript-eslint";

export default [
  {
    files: ["src/**/*.ts", "src/**/*.tsx", "tests/**/*.ts", "tests/**/*.tsx"],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: "./tsconfig.json"
      },
      ecmaVersion: 2022,
      sourceType: "module"
    },
    rules: {
      "no-var": "error",
      "prefer-const": "error"
    }
  }
];
