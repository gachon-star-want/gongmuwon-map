import React from 'react';
import ReactDOM from 'react-dom/client';
import { createTheme, MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import './styles.css';
import { App } from './App';

const theme = createTheme({
  fontFamily:
    "'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  primaryColor: 'brand',
  colors: {
    brand: [
      '#EEF2FF', '#E0E8FF', '#C7D4F7', '#A5B8F0',
      '#7B96E6', '#5174DA', '#2B4589', '#1A2E5A',
      '#142446', '#0E1A33',
    ],
  },
  defaultRadius: 'sm',
  components: {
    TextInput: {
      defaultProps: { size: 'sm' },
      styles: {
        input: { height: 'var(--control-height-lg)', borderColor: 'var(--color-border-mid)' },
      },
    },
    Select: {
      defaultProps: { size: 'sm' },
      styles: {
        input: { height: 'var(--control-height)', borderColor: 'var(--color-border-mid)' },
      },
    },
    MultiSelect: {
      defaultProps: { size: 'sm' },
      styles: {
        input: { minHeight: 'var(--control-height)', borderColor: 'var(--color-border-mid)' },
      },
    },
    Button: {
      defaultProps: { size: 'sm' },
      styles: { root: { height: 'var(--control-height)', fontWeight: 700 } },
    },
    ActionIcon: {
      defaultProps: { size: 'sm', variant: 'subtle' },
      styles: { root: { width: 'var(--control-height)', height: 'var(--control-height)' } },
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="auto">
      <App />
    </MantineProvider>
  </React.StrictMode>,
);
