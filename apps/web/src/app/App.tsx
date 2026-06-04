import type { ReactElement } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { CommunityPage } from '../features/community/CommunityPage';
import { PlaceExplorer } from '../features/place-explorer/PlaceExplorer';
import { StaticPage } from './staticPages';

const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

export function App(): ReactElement {
  const path = window.location.pathname;
  
  let content: ReactElement;
  if (staticPaths.has(path)) {
    content = <StaticPage path={path} />;
  } else if (path === '/community') {
    content = <CommunityPage />;
  } else {
    content = <PlaceExplorer />;
  }
  
  return (
    <>
      <ErrorBoundary key={path}>{content}</ErrorBoundary>
      <Analytics />
    </>
  );
}
