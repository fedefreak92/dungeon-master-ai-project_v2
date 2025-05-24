const path = require('path');

module.exports = {
  // Manteniamo la configurazione di base da react-scripts
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      return webpackConfig;
    },
  },
  // Configurazione specifica per webpack-dev-server
  devServer: {
    allowedHosts: 'all', // Risolve il problema options.allowedHosts[0]
    host: 'localhost',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        pathRewrite: { '^/api': '' },
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
    },
  },
}; 