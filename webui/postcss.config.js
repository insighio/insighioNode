// const IN_PRODUCTION = process.env.NODE_ENV === "production"

// export default {
//   plugins: [
//     IN_PRODUCTION &&
//       require("@fullhuman/postcss-purgecss")({
//         content: [`./public/**/*.html`, `./src/**/*.vue`, `./src/**/*.css`],
//         defaultExtractor(content) {
//           const contentWithoutStyleBlocks = content.replace(/<style[^]+?<\/style>/gi, "")
//           return contentWithoutStyleBlocks.match(/[A-Za-z0-9-_/:]*[A-Za-z0-9-_/]+/g) || []
//         },
//         safelist: [
//           /-(leave|enter|appear)(|-(to|from|active))$/,
//           /^(?!(|.*?:)cursor-move).+-move$/,
//           /^router-link(|-exact)-active$/,
//           /data-v-.*/
//         ]
//       })
//   ]
// }
////////////////////

import pkg from "@fullhuman/postcss-purgecss"

const IN_PRODUCTION = process.env.NODE_ENV === "production"

export default {
  plugins: [
    ...(IN_PRODUCTION
      ? [
          pkg({
            // Only scan templates/scripts for used selectors.
            // Including CSS files here prevents effective purging.
            content: [`./index.html`, `./public/**/*.html`, `./src/**/*.{vue,js,ts}`],
            defaultExtractor(content) {
              const contentWithoutStyleBlocks = content.replace(/<style[^]+?<\/style>/gi, "")
              return contentWithoutStyleBlocks.match(/[A-Za-z0-9-_/:]*[A-Za-z0-9-_/]+/g) || []
            },
            safelist: {
              standard: [
                /-(leave|enter|appear)(|-(to|from|active))$/,
                /^(?!(|.*?:)cursor-move).+-move$/,
                /^router-link(|-exact)-active$/,
                /data-v-.*/,
                // Dynamically generated grid classes in templates.
                /^col-\d+$/,
                /^col-(xs|sm|md|lg|xl)-\d+$/,
                /^column$/,
                /^columns$/
              ],
              deep: [],
              greedy: [
                // Keep Spectre divider variants used by SDivider data-content labels.
                /divider/,
                /data-content/
              ]
            }
          })
        ]
      : [])
  ]
}
