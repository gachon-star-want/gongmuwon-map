import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary:', error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            minWidth: '100vw',
            padding: '24px',
            textAlign: 'center',
          }}
        >
          <h2 style={{ marginBottom: '12px', fontSize: '20px', fontWeight: 700 }}>
            문제가 발생했습니다
          </h2>
          <p style={{ marginBottom: '24px', color: '#666', fontSize: '14px' }}>
            예기치 않은 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
          </p>
          <button
            type="button"
            style={{
              padding: '10px 24px',
              fontSize: '14px',
              fontWeight: 600,
              color: '#fff',
              backgroundColor: '#228be6',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            다시 시도
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
