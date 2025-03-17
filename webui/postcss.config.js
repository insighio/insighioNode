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

export default {
  plugins: [
    pkg({
      content: [`./public/**/*.html`, `./src/**/*.vue`, `./src/**/*.css`],
      defaultExtractor(content) {
        const contentWithoutStyleBlocks = content.replace(/<style[^]+?<\/style>/gi, "")
        return contentWithoutStyleBlocks.match(/[A-Za-z0-9-_/:]*[A-Za-z0-9-_/]+/g) || []
      },
      safelist: [
        /-(leave|enter|appear)(|-(to|from|active))$/,
        /^(?!(|.*?:)cursor-move).+-move$/,
        /^router-link(|-exact)-active$/,
        /data-v-.*/
      ]
    })
  ]
}
