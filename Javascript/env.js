export function getEnvVar(name) {
  const vars = {
    API_BASE_URL: 'https://your-production-api-url.com'
  };
  return vars[name];
}
