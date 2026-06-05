import { LogIn, MapPin, MessageCircle, UserRound } from 'lucide-react';
import type { CurrentUser } from '../features/auth/authApi';
import mascotLogo from '../assets/officer-mascot-logo.png';

interface PanelHeaderProps {
  activePage: 'map' | 'community';
  currentUser?: CurrentUser | null;
  onLogin?: () => void;
  onLogout?: () => void;
}

export function PanelHeader({ activePage, currentUser, onLogin, onLogout }: PanelHeaderProps) {
  return (
    <header className="panel-header">
      <a className="panel-brand" href="/" aria-label="공무원맵 홈">
        <img src={mascotLogo} alt="" aria-hidden width={28} height={28} />
        <span>공무원맵</span>
      </a>
      <nav className="panel-nav" aria-label="페이지 탐색">
        <a href="/" className="panel-nav-tab" data-active={activePage === 'map'}>
          <MapPin size={15} aria-hidden />
          지도
        </a>
        <a href="/community" className="panel-nav-tab" data-active={activePage === 'community'}>
          <MessageCircle size={15} aria-hidden />
          커뮤니티
        </a>
      </nav>
      <div className="panel-header-auth">
        {currentUser ? (
          <button className="panel-auth-btn" onClick={onLogout}>
            <UserRound size={14} />
            {currentUser.handle}
          </button>
        ) : (
          <button className="panel-auth-btn" onClick={onLogin}>
            <LogIn size={14} />
            로그인
          </button>
        )}
      </div>
    </header>
  );
}
