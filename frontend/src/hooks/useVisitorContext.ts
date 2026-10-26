import { useState, useEffect, useCallback } from 'react';
import { visitorApi } from '../api/visitor';
import type { VisitorProfile, ConsentCategory, ConsentStatus } from '../types/visitor';

const STORAGE_KEY = 'caldim_visitor_session_v1';

interface StoredSession {
  visitor: VisitorProfile;
  token: string;
}

export function useVisitorContext() {
  const [visitor, setVisitor] = useState<VisitorProfile | null>(null);
  const [token, setToken] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Restore session from localStorage and verify against backend, or create new guest session
  useEffect(() => {
    async function initSession() {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          try {
            const parsed: StoredSession = JSON.parse(stored);
            if (parsed.visitor && parsed.token) {
              // Verify token validity against backend and fetch latest state
              const verified = await visitorApi.getVisitorProfile(parsed.visitor.id, parsed.token);
              setVisitor(verified.visitor);
              setToken(parsed.token);
              const sessionData: StoredSession = {
                visitor: verified.visitor,
                token: parsed.token,
              };
              localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
              setIsLoading(false);
              return;
            }
          } catch (sessionErr) {
            // Stored token invalid/expired, fall through to create new guest profile
            localStorage.removeItem(STORAGE_KEY);
          }
        }

        // Initialize single guest visitor profile
        const newVisitor = await visitorApi.createVisitor({
          display_name: '',
          profession: '',
          company_name: '',
          industry: '',
          initial_consents: [
            {
              category: 'essential' as ConsentCategory,
              status: 'granted' as ConsentStatus,
            },
          ],
        });

        const sessionData: StoredSession = {
          visitor: newVisitor.visitor,
          token: newVisitor.access_token,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
        setVisitor(newVisitor.visitor);
        setToken(newVisitor.access_token);
      } catch (err: unknown) {
        setError('Failed to establish visitor context. Ensure backend is running.');
      } finally {
        setIsLoading(false);
      }
    }

    initSession();
  }, []);

  const updateProfile = useCallback(
    async (profileData: {
      displayName?: string;
      email?: string;
      phone?: string;
      profession?: string;
      companyName?: string;
      industry?: string;
      department?: string;
      responsibilities?: string;
      // also allow snake_case directly
      display_name?: string;
      company_name?: string;
    }) => {
      if (!visitor || !token) return;

      try {
        const payload = {
          display_name: profileData.displayName ?? profileData.display_name,
          email: profileData.email,
          phone: profileData.phone,
          profession: profileData.profession,
          company_name: profileData.companyName ?? profileData.company_name,
          industry: profileData.industry,
          department: profileData.department,
          responsibilities: profileData.responsibilities,
        };

        // Filter undefined values
        const cleanPayload = Object.fromEntries(
          Object.entries(payload).filter(([_, v]) => v !== undefined)
        );

        // Update existing visitor profile via PATCH (prevents duplicate visitor records)
        const res = await visitorApi.updateVisitorProfile(visitor.id, token, cleanPayload);

        const sessionData: StoredSession = {
          visitor: res.visitor,
          token: token,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
        setVisitor(res.visitor);
        return res.visitor;
      } catch (err) {
        throw err;
      }
    },
    [token, visitor]
  );

  const resetSession = useCallback(async () => {
    localStorage.removeItem(STORAGE_KEY);
    setVisitor(null);
    setToken('');
    setIsLoading(true);

    try {
      const newVisitor = await visitorApi.createVisitor({
        display_name: '',
        profession: '',
        company_name: '',
        industry: '',
        initial_consents: [
          {
            category: 'essential' as ConsentCategory,
            status: 'granted' as ConsentStatus,
          },
        ],
      });

      const sessionData: StoredSession = {
        visitor: newVisitor.visitor,
        token: newVisitor.access_token,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
      setVisitor(newVisitor.visitor);
      setToken(newVisitor.access_token);
    } catch (err) {
      setError('Failed to establish visitor context.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    visitor,
    token,
    isLoading,
    error,
    updateProfile,
    resetSession,
  };
}
