// .eslintrc.js
module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: [
    //"plugin:prettier-vue/recommended",
    // Do not add `'prettier/vue'` if you don't want to use prettier for `<template>` blocks
    //"prettier/vue",
    "plugin:prettier/recommended",
    "prettier"
  ],

  settings: {
    "prettier/prettier": {
      // Settings for how to process Vue SFC Blocks
      SFCBlocks: {
        /**
         * Use prettier to process `<template>` blocks or not
         *
         * If set to `false`, remember not to `extends: ['prettier/vue']`, as you need the rules from `eslint-plugin-vue` to lint `<template>` blocks
         *
         * @default true
         */
        template: true,

        /**
         * Use prettier to process `<script>` blocks or not
         *
         * @default true
         */
        script: true,

        /**
         * Use prettier to process `<style>` blocks or not
         *
         * @default true
         */
        style: true,

        // Settings for how to process custom blocks
        customBlocks: {
          // Treat the `<docs>` block as a `.markdown` file
          docs: { lang: "markdown" },

          // Treat the `<config>` block as a `.json` file
          config: { lang: "json" },

          // Treat the `<module>` block as a `.js` file
          module: { lang: "js" },

          // Ignore `<comments>` block (omit it or set it to `false` to ignore the block)
          comments: false

          // Other custom blocks that are not listed here will be ignored
        }
      },

      // Use prettierrc for prettier options or not (default: `true`)
      usePrettierrc: true,

      // Set the options for `prettier.getFileInfo`.
      // @see https://prettier.io/docs/en/api.html#prettiergetfileinfofilepath-options
      fileInfoOptions: {
        // Path to ignore file (default: `'.prettierignore'`)
        // Notice that the ignore file is only used for this plugin
        ignorePath: ".testignore",

        // Process the files in `node_modules` or not (default: `false`)
        withNodeModules: false
      }
    }
  },

  rules: {
    "prettier/prettier": [
      "error",
      {
        // Override all options of `prettier` here
        // @see https://prettier.io/docs/en/options.html
        printWidth: 120,
        singleQuote: false,
        semi: false,
        trailingComma: "none",
        tabWidth: 2
      }
    ]
  }
  // globals: {
  //   $nuxt: true
  // }
  // parserOptions: {
  //   parser: "babel-eslint"
  // }
}
