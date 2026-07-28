/* global.css va importato per primo: definisce le classi di base (.card, .btn)
   che i fogli di stile dei componenti devono poter sovrascrivere. */
import './styles/global.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { AppProvider } from './state/AppContext';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </StrictMode>,
);
