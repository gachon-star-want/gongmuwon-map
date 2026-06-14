import type { ReactElement } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { AppShell } from './AppShell';
import { CommunityPage } from '../features/community/CommunityPage';
import { NeighborhoodPage } from '../features/neighborhood/NeighborhoodPage';
import { PlaceExplorer } from '../features/place-explorer/PlaceExplorer';
import { StaticPage } from './staticPages';

const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

export function App(): ReactElement {
  const path = window.location.pathname;
  
  if (staticPaths.has(path)) {
    return (
      <>
        <ErrorBoundary key={path}><StaticPage path={path} /></ErrorBoundary>
        <Analytics />
      </>
    );
  }

  if (path === '/community') {
    return (
      <>
        <ErrorBoundary key={path}><CommunityPage /></ErrorBoundary>
        <Analytics />
      </>
    );
  }

  if (path === '/neighborhood') {
    return (
      <>
        <ErrorBoundary key={path}><NeighborhoodPage /></ErrorBoundary>
        <Analytics />
      </>
    );
  }

  return (
    <>
      <AppShell>
        <ErrorBoundary key={path}>
          <PlaceExplorer />
        </ErrorBoundary>
      </AppShell>
      <Analytics />
    </>
  );
}
