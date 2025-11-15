export const initAnalytics = (measurementId: string) => {
  if (!measurementId || typeof window === 'undefined') {
    return;
  }

  if (document.getElementById('ga-script')) {
    return;
  }

  const script = document.createElement('script');
  script.async = true;
  script.id = 'ga-script';
  script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
  document.head.appendChild(script);

  window.dataLayer = window.dataLayer || [];
  function gtag(...args: unknown[]) {
    window.dataLayer.push(args);
  }
  gtag('js', new Date());
  gtag('config', measurementId);
};

declare global {
  interface Window {
    dataLayer: unknown[];
  }
}
