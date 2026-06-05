import type { ReactNode } from 'react';
import { PanelHeader } from './PanelHeader';

const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

export function AppShell({ children }: { children: ReactNode }) {
  const path = window.location.pathname;
  const isMap = !staticPaths.has(path) && path !== '/community' && path !== '/';
  const isCommunity = path === '/community';
  const isHome = path === '/';

  const activePage = isCommunity ? 'community' : 'map';

  return (
    <div className="app-shell">
      <div className="left-panel">
        <PanelHeader activePage={activePage} />
        <div className="panel-body">
          {children}
        </div>
      </div>
      {(isHome || isMap) && (
        <main className="map-area" id="map-area" aria-label="지도" />
      )}
    </div>
  );
}
