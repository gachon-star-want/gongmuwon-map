import type { ReactElement } from 'react';
import { CommunityPage } from '../features/community/CommunityPage';
import { PlaceExplorer } from '../features/place-explorer/PlaceExplorer';
import { StaticPage } from './staticPages';

const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

export function App(): ReactElement {
  const path = window.location.pathname;
  if (staticPaths.has(path)) {
    return <StaticPage path={path} />;
  }
  if (path === '/community') {
    return <CommunityPage />;
  }
  return <PlaceExplorer />;
}
