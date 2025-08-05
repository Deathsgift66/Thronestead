const ENDPOINT = '/api/logs/error';

function send(data) {
  try {
    const body = JSON.stringify(data);
    if (navigator.sendBeacon) {
      navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'application/json' }));
    } else {
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      });
    }
  } catch (err) {
    if (typeof import !== 'undefined' && import.meta?.env?.DEV) {
      console.warn('Error reporting failed:', err);
    }
  }
}

function handle(err, context) {
  if (window.Sentry?.captureException) {
    window.Sentry.captureException(err);
    return;
  }
  const e = err instanceof Error ? err : new Error(String(err));
  send({
    message: e.message,
    stack: e.stack || '',
    context,
    url: location.href,
    user_agent: navigator.userAgent,
    timestamp: Date.now(),
  });
}

window.addEventListener('error', (e) => handle(e.error || e, 'error'));
window.addEventListener('unhandledrejection', (e) => handle(e.reason, 'promise'));

export { handle as reportError };

