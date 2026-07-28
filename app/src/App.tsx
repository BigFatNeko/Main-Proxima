import { useApp } from './state/AppContext';
import LoginScreen from './screens/LoginScreen';
import QuestionarioScreen from './screens/QuestionarioScreen';
import ConsulenteScreen from './screens/ConsulenteScreen';
import DashboardScreen from './screens/DashboardScreen';

export default function App() {
  const { schermata } = useApp();

  switch (schermata) {
    case 'login':
      return <LoginScreen />;
    case 'questionario':
      return <QuestionarioScreen />;
    case 'consulente':
      return <ConsulenteScreen />;
    case 'dashboard':
      return <DashboardScreen />;
  }
}
