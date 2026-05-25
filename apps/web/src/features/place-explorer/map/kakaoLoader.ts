export function loadKakao(appKey: string) {
  if (window.kakao?.maps?.MarkerClusterer) {
    return Promise.resolve();
  }
  return new Promise<void>((resolve, reject) => {
    let settled = false;
    const timeout = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      reject(new Error('kakao map timeout'));
    }, 4500);
    const done = () => {
      if (settled) return;
      try {
        window.kakao.maps.load(() => {
          if (settled) return;
          settled = true;
          window.clearTimeout(timeout);
          resolve();
        });
      } catch {
        settled = true;
        window.clearTimeout(timeout);
        reject(new Error('kakao map failed'));
      }
    };
    const failed = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeout);
      reject(new Error('kakao map failed'));
    };
    const existing = document.querySelector<HTMLScriptElement>('script[data-kakao-map]');
    if (existing) {
      existing.addEventListener('load', done);
      existing.addEventListener('error', failed);
      return;
    }
    const script = document.createElement('script');
    script.dataset.kakaoMap = 'true';
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&libraries=clusterer&autoload=false`;
    script.async = true;
    script.onload = done;
    script.onerror = failed;
    document.head.appendChild(script);
  });
}

declare global {
  interface Window {
    kakao: any;
  }
}
