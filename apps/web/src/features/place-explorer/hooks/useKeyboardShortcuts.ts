import { useEffect } from 'react';

interface UseKeyboardShortcutsOptions {
  isModalOpen: boolean;
  hasSelection: boolean;
  isDesktopListOpen: boolean;
  isMobilePanelOpen: boolean;
  onClearSelection: () => void;
  onCloseDesktopList: () => void;
  onCloseMobilePanel: () => void;
}

export function useKeyboardShortcuts({
  isModalOpen,
  hasSelection,
  isDesktopListOpen,
  isMobilePanelOpen,
  onClearSelection,
  onCloseDesktopList,
  onCloseMobilePanel,
}: UseKeyboardShortcutsOptions) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        (event.target as HTMLElement).isContentEditable
      ) {
        return;
      }
      if (isModalOpen) return;
      if (hasSelection) {
        onClearSelection();
        return;
      }
      if (isDesktopListOpen) {
        onCloseDesktopList();
        return;
      }
      if (isMobilePanelOpen) {
        onCloseMobilePanel();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isModalOpen, hasSelection, isDesktopListOpen, isMobilePanelOpen, onClearSelection, onCloseDesktopList, onCloseMobilePanel]);
}
