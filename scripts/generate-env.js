const fs = require('fs');
const path = require('path');
require('dotenv').config();

const env = {
  API_BASE_URL: process.env.API_BASE_URL,
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY,
};

fs.writeFileSync(path.join(__dirname, '../public/env.js'), `window.ENV = ${JSON.stringify(env, null, 2)};`);
console.log('✅ env.js generated');
