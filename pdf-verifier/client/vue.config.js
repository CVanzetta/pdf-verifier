const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  transpileDependencies: true,

  chainWebpack: config => {
    config.plugin('eslint')
      .use('eslint-webpack-plugin', [{}]);
  },

  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        '__VUE_PROD_HYDRATION_MISMATCH_DETAILS__': JSON.stringify(false),
      }),
    ],
    module: {
      rules: [
        {
          test: /pdf\.worker\.js$/,
          use: 'file-loader',
        },
      ],
    },
  },
});