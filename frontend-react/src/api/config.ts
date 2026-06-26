let _apiBase: string | null = null;

export async function getApiBase(): Promise<string> {
  if (_apiBase === null) {
    try {
      const res = await fetch('/config.json');
      const cfg = await res.json();
      _apiBase = cfg.apiBaseUrl || '';
    } catch {
      _apiBase = '';  // fallback: same origin
    }
  }
  return _apiBase;
}

// Synchronous version (safe to call after getApiBase() resolves)
export function getApiBaseSync(): string {
  return _apiBase ?? '';
}
