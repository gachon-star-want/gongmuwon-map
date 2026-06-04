const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  await page.setBypassCSP(true);

  // Print all browser console logs
  page.on('console', msg => {
    console.log(`[BROWSER CONSOLE] [${msg.type()}] ${msg.text()}`);
  });

  // Print page errors
  page.on('pageerror', err => {
    console.error(`[BROWSER ERROR] ${err.toString()}`);
  });

  // Inject Mock Geolocation and Mock Kakao Maps before load
  await page.evaluateOnNewDocument(() => {
    // 1. Mock Geolocation
    navigator.geolocation.getCurrentPosition = (success, error, options) => {
      console.log('[MOCK GEOLOCATION] getCurrentPosition invoked. Triggering success in 500ms (Bokjeong-dong)...');
      setTimeout(() => {
        success({
          coords: {
            latitude: 37.4526, // Bokjeong-dong Lat
            longitude: 127.1309, // Bokjeong-dong Lng
            accuracy: 10,
            altitude: null,
            altitudeAccuracy: null,
            heading: null,
            speed: null
          },
          timestamp: Date.now()
        });
      }, 500);
    };

    // 2. Mock Kakao Maps API
    const listeners = new Map();
    const mockKakao = {
      maps: {
        LatLng: function(lat, lng) {
          this.lat = lat;
          this.lng = lng;
          this.getLat = () => this.lat;
          this.getLng = () => this.lng;
        },
        LatLngBounds: function(sw, ne) {
          this.sw = sw;
          this.ne = ne;
          this.getSouthWest = () => this.sw;
          this.getNorthEast = () => this.ne;
        },
        Size: function(width, height) {
          this.width = width;
          this.height = height;
        },
        Point: function(x, y) {
          this.x = x;
          this.y = y;
        },
        MarkerImage: function(src, size, options) {
          this.src = src;
          this.size = size;
          this.options = options;
        },
        Map: function(element, options) {
          this.center = options.center;
          this.level = options.level;
          this.getCenter = () => this.center;
          this.getLevel = () => this.level;
          this.getBounds = () => {
            // Return dummy bounds shifted around the center
            const lat = this.center.getLat();
            const lng = this.center.getLng();
            return new mockKakao.maps.LatLngBounds(
              new mockKakao.maps.LatLng(lat - 0.01, lng - 0.01),
              new mockKakao.maps.LatLng(lat + 0.01, lng + 0.01)
            );
          };
          this.setCenter = (latlng) => {
            this.center = latlng;
            console.log(`[MOCK MAP] setCenter to lat: ${latlng.getLat()}, lng: ${latlng.getLng()}`);
            // Trigger idle event when center is updated
            setTimeout(() => {
              const list = listeners.get(this) || {};
              if (list['idle']) {
                console.log('[MOCK MAP] Triggering idle event...');
                list['idle']();
              }
            }, 100);
          };
          this.setLevel = (level) => {
            this.level = level;
            console.log(`[MOCK MAP] setLevel to: ${level}`);
          };
        },
        MarkerClusterer: function() {
          this.clear = () => {};
          this.addMarkers = () => {};
        },
        Marker: function(options) {
          this.position = options.position;
          this.setMap = () => {};
          this.setPosition = () => {};
          this.setImage = () => {};
          this.setZIndex = () => {};
        },
        event: {
          addListener: (target, event, callback) => {
            if (!listeners.has(target)) {
              listeners.set(target, {});
            }
            listeners.get(target)[event] = callback;
          },
          removeListener: () => {}
        },
        load: (callback) => {
          console.log('[MOCK KAKAO] Load triggered, executing callback immediately...');
          callback();
        }
      }
    };

    window.kakao = mockKakao;
  });

  // Request & response logging
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/api/v1/places')) {
      console.log(`[BROWSER FETCH] Request: ${url}`);
    }
  });

  // Track response results
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/v1/places')) {
      try {
        const text = await response.text();
        console.log(`[BROWSER FETCH] Response to ${url}: status ${response.status()}, body length: ${text.length}`);
      } catch (err) {
        console.log(`[BROWSER FETCH] Error reading response body for ${url}: ${err.message}`);
      }
    }
  });

  console.log('Navigating to http://localhost:3000...');
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });

  console.log('Waiting 5 seconds for map bounds & geolocation callbacks to settle...');
  await new Promise(resolve => setTimeout(resolve, 5000));

  console.log('Closing browser...');
  await browser.close();
  process.exit(0);
})().catch(err => {
  console.error('Test script crashed:', err);
  process.exit(1);
});
