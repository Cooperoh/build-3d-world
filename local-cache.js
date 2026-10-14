// Local archival adapter. The saved original HTML is unchanged on disk.
(() => {
  const originalFetch = window.fetch.bind(window);
  const hosts = new Set(['tools.oyasumi-gamedev.com', 'tiles.openfreemap.org', 's3.amazonaws.com', 'cyberjapandata.gsi.go.jp', 'nominatim.openstreetmap.org']);
  window.fetch = function(input, init) {
    const request = input instanceof Request ? input : null;
    const url = new URL(request ? request.url : String(input), location.href);
    const method = (init?.method || request?.method || 'GET').toUpperCase();
    if (method === 'GET' && url.protocol === 'https:' && hosts.has(url.hostname)) {
      return originalFetch('/__proxy?url=' + encodeURIComponent(url.href), {...init, signal: init?.signal || request?.signal});
    }
    return originalFetch(input, init);
  };
})();
