module.exports = {
  devServer: {
    headers: {
      "Cache-Control": "no-cache, no-store, must-revalidate",
      Pragma: "no-cache",
      Expires: "0"
    }
  },
  chainWebpack: (config) => {
    // Add timestamp to filenames for cache busting
    config.output.filename("[name].[contenthash:8].js")
    config.output.chunkFilename("[name].[contenthash:8].js")
  },
  // Disable file hashing in production for consistent filenames
  filenameHashing: process.env.NODE_ENV !== "production"
}
