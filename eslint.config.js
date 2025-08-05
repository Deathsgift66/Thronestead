export default [
  {
    ignores: ['dist/**', 'node_modules/**']
  },
  {
    files: ['Javascript/**/*.js', 'supabase-client.js'],
    languageOptions: {
      sourceType: 'module',
      ecmaVersion: 2022,
      globals: {
        document: 'readonly',
        window: 'readonly',
        navigator: 'readonly',
        console: 'readonly',
        alert: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        URL: 'readonly',
        URLSearchParams: 'readonly',
        WebSocket: 'readonly',
        requestAnimationFrame: 'readonly',
        cancelAnimationFrame: 'readonly',
        EventSource: 'readonly',
        AbortController: 'readonly',
        prompt: 'readonly',
        confirm: 'readonly',
        atob: 'readonly',
        sessionStorage: 'readonly',
        localStorage: 'readonly',
        location: 'readonly',
        Image: 'readonly',
        IntersectionObserver: 'readonly',
        d3: 'readonly',
        gsap: 'readonly'
      }
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-undef': 'error'
    }
  },
  {
    files: ['scripts/*.js', 'vite.config.js'],
    languageOptions: {
      sourceType: 'module',
      ecmaVersion: 2022,
      globals: {
        require: 'readonly',
        module: 'readonly',
        process: 'readonly',
        __dirname: 'readonly',
        console: 'readonly'
      }
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-undef': 'error'
    }
  }
];
