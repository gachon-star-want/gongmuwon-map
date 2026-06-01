import type { ReactElement } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { CommunityPage } from '../features/community/CommunityPage';
import { PlaceExplorer } from '../features/place-explorer/PlaceExplorer';
import { StaticPage } from './staticPages';

const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

export function App(): ReactElement {
  const path = window.location.pathname;
  if (staticPaths.has(path)) {
    return (
      <>
        <StaticPage path={path} />
        <Analytics />
      </>
    );
  }
  if (path === '/community') {
    return (
      <>
        <CommunityPage />
        <Analytics />
      </>
    );
  }
  return (
    <>
      <PlaceExplorer />
      <Analytics />
    </>
  );
}
