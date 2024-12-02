const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,

  chainWebpack: config => {
    config.plugin('eslint')
      .use('eslint-webpack-plugin', [{}]);
  },
});
