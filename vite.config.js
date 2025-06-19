import { resolve } from 'path';

export default {
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        signup: resolve(__dirname, 'signup.html'),
        login: resolve(__dirname, 'login.html'),
        about: resolve(__dirname, 'about.html')
      }
    }
  }
};
