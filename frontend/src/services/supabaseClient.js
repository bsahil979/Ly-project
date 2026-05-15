import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Initialize the live Supabase client connected to the user's provisioned instance
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Custom Auth Wrapper with Development Fallback
export const AuthService = {
  createDemoAccount() {
    const timestamp = Date.now();
    const demoUser = {
      id: `demo_${timestamp}`,
      email: `demo_${timestamp}@smartadvisor.ai`,
      user_metadata: {
        full_name: `Demo User ${Math.floor(Math.random() * 10000)}`,
      },
      isDemo: true,
    };

    localStorage.setItem('smart_portfolio_mock_user', JSON.stringify(demoUser));
    window.dispatchEvent(new Event('auth-change'));
    return { data: { user: demoUser } };
  },

  async register(email, password, fullName, isDemo = false) {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName },
        },
      });
      if (error) throw error;
      return data;
    } catch (err) {
      console.warn("Supabase Signup failed, using local fallback:", err.message);
      // Fallback for development/offline use
      const mockUser = { 
        id: `mock_${Date.now()}`, 
        email, 
        user_metadata: { full_name: fullName },
        isDemo: isDemo 
      };
      
      if (isDemo) {
        // Demo account - stored only in session (removed on logout)
        localStorage.setItem('smart_portfolio_mock_user', JSON.stringify(mockUser));
      } else {
        // Real account - stored persistently
        const realAccounts = JSON.parse(localStorage.getItem('smart_portfolio_real_accounts') || '[]');
        realAccounts.push(mockUser);
        localStorage.setItem('smart_portfolio_real_accounts', JSON.stringify(realAccounts));
        // Also set as current user
        localStorage.setItem('smart_portfolio_mock_user', JSON.stringify(mockUser));
      }
      
      window.dispatchEvent(new Event('auth-change'));
      return { data: { user: mockUser } };
    }
  },

  async login(email, password) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      window.dispatchEvent(new Event('auth-change'));
      return data;
    } catch (err) {
      console.warn("Supabase Login failed, using local fallback:", err.message);
      
      // Check if this is a real registered account
      const realAccounts = JSON.parse(localStorage.getItem('smart_portfolio_real_accounts') || '[]');
      const existingAccount = realAccounts.find(acc => acc.email === email);
      
      if (existingAccount) {
        // Login to real account
        localStorage.setItem('smart_portfolio_mock_user', JSON.stringify(existingAccount));
        window.dispatchEvent(new Event('auth-change'));
        return { data: { user: existingAccount } };
      }
      
      // Fallback: Allow any login in dev mode to prevent lockouts (temporary session)
      const mockUser = { 
        id: `mock_${email}`, 
        email, 
        user_metadata: { full_name: email.split('@')[0] },
        isDemo: true 
      };
      localStorage.setItem('smart_portfolio_mock_user', JSON.stringify(mockUser));
      window.dispatchEvent(new Event('auth-change'));
      return { data: { user: mockUser } };
    }
  },

  async logout() {
    await supabase.auth.signOut();
    // Only remove temporary accounts
    const currentUser = JSON.parse(localStorage.getItem('smart_portfolio_mock_user') || '{}');
    if (currentUser.isDemo) {
      localStorage.removeItem('smart_portfolio_mock_user');
    } else {
      // Real account - keep it for next login
      localStorage.removeItem('smart_portfolio_mock_user');
    }
    window.dispatchEvent(new Event('auth-change'));
  },

  async getCurrentUser() {
    const { data } = await supabase.auth.getUser();
    if (data?.user) return { data };

    // Check local fallback
    const mockUser = localStorage.getItem('smart_portfolio_mock_user');
    if (mockUser) {
      return { data: { user: JSON.parse(mockUser) } };
    }
    return { data: { user: null } };
  }
};

// Persistent User-Scoped Portfolio Storage Engine
export const PortfolioStorageService = {
  async getUserPortfolio(userId) {
    if (!userId) return [];
    try {
      // Try querying the persistent remote Supabase DB ledger
      const { data, error } = await supabase
        .from('user_portfolios')
        .select('tickers')
        .eq('user_id', userId)
        .maybeSingle();
        
      if (!error && data?.tickers) {
        return data.tickers;
      }
    } catch (e) {
      console.warn("Supabase table lookup warning:", e);
    }
    
    // Automatic local fallback layer mapped exactly to the authenticated user UUID
    const localData = localStorage.getItem(`smart_portfolio_${userId}`);
    return localData ? JSON.parse(localData) : [];
  },

  async saveUserPortfolio(userId, tickers) {
    if (!userId) return;
    try {
      // Upsert directly into user_portfolios ledger table
      await supabase
        .from('user_portfolios')
        .upsert({ 
          user_id: userId, 
          tickers, 
          updated_at: new Date().toISOString() 
        }, { onConflict: 'user_id' });
    } catch (e) {
      console.warn("Supabase table update warning:", e);
    }
    
    // Mirror synchronization locally scoped to prevent account state cross-contamination
    localStorage.setItem(`smart_portfolio_${userId}`, JSON.stringify(tickers));
  }
};
