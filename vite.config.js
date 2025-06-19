import { resolve } from 'path';

export default {
  build: {
    outDir: 'dist',
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
