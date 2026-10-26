import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { ShowroomView } from './features/showroom/ShowroomView';
import { ConsultationWorkspace } from './features/consultation/ConsultationWorkspace';
import { SystemStatusView } from './features/system-status/SystemStatusView';
import { useSystemHealth } from './hooks/useSystemHealth';
import { useVisitorContext } from './hooks/useVisitorContext';

export const App: React.FC = () => {
  const { state: apiStatus } = useSystemHealth({ autoRefresh: true, intervalMs: 15000 });
  const { visitor, token, updateProfile } = useVisitorContext();

  const [activeTab, setActiveTab] = useState<'showroom' | 'consultation' | 'diagnostics'>('showroom');
  const [pendingChallenge, setPendingChallenge] = useState<string | undefined>(undefined);

  const handleStartConsultation = (challenge: string) => {
    setPendingChallenge(challenge);
    setActiveTab('consultation');
  };

  const visitorLabel = visitor?.display_name
    ? `${visitor.display_name}${visitor.company_name ? ` @ ${visitor.company_name}` : ''}`
    : visitor?.profession || 'Exhibition Guest';

  return (
    <>
      <Header
        apiStatus={apiStatus}
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
          if (tab !== 'consultation') {
            setPendingChallenge(undefined);
          }
        }}
        visitorLabel={visitorLabel}
      />

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'showroom' && (
          <ShowroomView onStartConsultation={handleStartConsultation} />
        )}

        {activeTab === 'consultation' && (
          <ConsultationWorkspace
            token={token}
            visitor={visitor}
            initialChallenge={pendingChallenge}
            onBackToShowroom={() => {
              setActiveTab('showroom');
              setPendingChallenge(undefined);
            }}
            onUpdateProfile={updateProfile}
          />
        )}

        {activeTab === 'diagnostics' && <SystemStatusView />}
      </main>

      <Footer />
    </>
  );
};

export default App;
