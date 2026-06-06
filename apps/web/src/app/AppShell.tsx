import { useEffect, useState, type ReactNode } from 'react';
import { PanelHeader } from './PanelHeader';
import { AuthModal } from '../features/auth/AuthModal';
import {
  AUTH_STATE_CHANGE_EVENT,
  getCurrentUser,
  logout,
  type AuthStateChangeDetail,
  type CurrentUser,
} from '../features/auth/authApi';

const staticPaths = new Set(['/about', '/privacy', '/terms', '/disclaimer', '/legal', '/api']);

export function AppShell({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const path = window.location.pathname;
  const isMap = !staticPaths.has(path) && path !== '/community' && path !== '/';
  const isCommunity = path === '/community';
  const isHome = path === '/';

  const activePage = isCommunity ? 'community' : 'map';

  useEffect(() => {
    void getCurrentUser()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));

    const onAuthStateChange = (event: Event) => {
      setCurrentUser((event as CustomEvent<AuthStateChangeDetail>).detail.user);
    };
    window.addEventListener(AUTH_STATE_CHANGE_EVENT, onAuthStateChange);
    return () => window.removeEventListener(AUTH_STATE_CHANGE_EVENT, onAuthStateChange);
  }, []);

  if (isHome || isMap) {
    return (
      <div className="app-shell">
        {children}
        <main className="map-area" id="map-area" aria-label="지도" />
        <AuthModal opened={authOpen} onClose={() => setAuthOpen(false)} onAuthenticated={setCurrentUser} />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="left-panel">
        <PanelHeader
          activePage={activePage}
          currentUser={currentUser}
          onLogin={() => setAuthOpen(true)}
          onLogout={() =>
            void logout()
              .then(() => setCurrentUser(null))
              .catch(() => setCurrentUser(null))
          }
        />
        <div className="panel-body">
          {children}
        </div>
      </div>
      <AuthModal opened={authOpen} onClose={() => setAuthOpen(false)} onAuthenticated={setCurrentUser} />
    </div>
  );
}
