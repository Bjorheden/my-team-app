// babel.config.js — required by Expo / jest-expo transformer
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
  };
};
