// eslint.config.mjs
import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginReact from 'eslint-plugin-react'
import pluginReactHooks from 'eslint-plugin-react-hooks'
import globals from 'globals'

export default [
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        sourceType: 'module',
        ecmaVersion: 2021,
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: globals.browser,
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
      react: pluginReact,
      'react-hooks': pluginReactHooks,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...tseslint.configs.recommended[0].rules,
      ...pluginReact.configs.recommended.rules,
      ...pluginReactHooks.configs.recommended.rules,

      // Custom overrides
      'no-console': 'warn',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-empty-interface': 'warn',
      'react/prop-types': 'off',
      'react/no-unescaped-entities': 'warn',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
]
