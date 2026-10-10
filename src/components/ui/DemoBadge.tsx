import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useBrand } from '../../context/BrandContext';
import { Sparkles, Shield, User, ArrowRightLeft, Check, Server, Database } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../../services/api/client';

export const DemoBadge: React.FC = () => {
  const { role, isDemoMode, switchRole, toggleDemoMode } = useAuth();
  const { brands, currentBrand, selectBrandById } = useBrand();
  const [isOpen, setIsOpen] = useState(false);
  const [dbConnected, setDbConnected] = useState<boolean>(false);
  const [dbEngine, setDbEngine] = useState<string>('postgresql');
  const navigate = useNavigate();

  useEffect(() => {
    const checkDb = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/ready`);
        if (res.ok) {
          const data = await res.json();
          setDbConnected(data?.dependencies?.database?.status === 'connected');
          if (data?.dependencies?.database?.engine) {
            setDbEngine(data.dependencies.database.engine);
          }
        } else {
          setDbConnected(false);
        }
      } catch {
        setDbConnected(false);
      }
    };
    checkDb();
    const interval = setInterval(checkDb, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative z-40">
      {/* Trigger Pill */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#111312] hover:bg-[#232524] border border-[#2B2D2C] text-xs font-semibold text-white shadow-sm transition-all duration-150 hover:scale-[1.02]"
        title="Toggle Demo Mode & Switch Test Personas"
      >
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FBF5A5] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FBF5A5]"></span>
        </span>
        <span className="font-bold text-[#FBF5A5]">
          {isDemoMode ? 'Demo Sandbox' : 'Live Mode'}
        </span>
        <span className="text-[10px] px-1.5 py-0.2 rounded-md bg-[#2B2D2C] text-[#D6D6D8] capitalize font-medium">
          {role === 'brand_owner' ? 'Brand Portal' : role === 'customer' ? 'Customer' : 'Public'}
        </span>
        <ArrowRightLeft className="w-3 h-3 ml-0.5 text-[#FBF5A5]/80" />
      </button>

      {/* Popover Menu */}
      {isOpen && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl border border-[#D5D4CE] shadow-2xl p-4 z-40 text-left animate-in fade-in slide-in-from-top-2 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-[#EAE9E4]">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-xl bg-[#111312] text-[#FBF5A5]">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#111312]">So-cio Demo Sandbox</h4>
                  <p className="text-[10px] text-[#737478]">Switch persona & backend integration</p>
                </div>
              </div>
            </div>

            {/* Quick Persona Switcher */}
            <div className="py-3 space-y-2">
              <p className="text-[11px] font-bold text-[#737478] uppercase tracking-wider">Switch Experience</p>
              
              <button
                onClick={() => {
                  switchRole('brand_owner');
                  setIsOpen(false);
                  navigate('/brand-owner/overview');
                }}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all ${
                  role === 'brand_owner' 
                    ? 'bg-[#111312] border-[#111312] text-[#FBF5A5] font-bold'
                    : 'bg-white hover:bg-[#F8F7F4] border-[#E2E1DC] text-[#111312]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Shield className="w-4 h-4" />
                  <div className="text-left">
                    <div>Brand Owner Portal</div>
                    <div className={`text-[10px] font-normal ${role === 'brand_owner' ? 'text-[#9A9B9C]' : 'text-[#737478]'}`}>ApexBank Global (Verified)</div>
                  </div>
                </div>
                {role === 'brand_owner' && <Check className="w-4 h-4 text-[#FBF5A5]" />}
              </button>

              <button
                onClick={() => {
                  switchRole('customer');
                  setIsOpen(false);
                  navigate('/customer');
                }}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all ${
                  role === 'customer' 
                    ? 'bg-[#111312] border-[#111312] text-[#FBF5A5] font-bold'
                    : 'bg-white hover:bg-[#F8F7F4] border-[#E2E1DC] text-[#111312]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <User className="w-4 h-4" />
                  <div className="text-left">
                    <div>Customer Portal</div>
                    <div className={`text-[10px] font-normal ${role === 'customer' ? 'text-[#9A9B9C]' : 'text-[#737478]'}`}>David Chen (Phone Verified)</div>
                  </div>
                </div>
                {role === 'customer' && <Check className="w-4 h-4 text-[#FBF5A5]" />}
              </button>
            </div>

            {/* Brand Switcher (When in Brand Owner Mode) */}
            {role === 'brand_owner' && brands.length > 0 && (
              <div className="pt-2 pb-3 border-t border-[#EAE9E4]">
                <p className="text-[11px] font-bold text-[#737478] uppercase tracking-wider mb-2">Active Brand Workspace</p>
                <div className="space-y-1">
                  {Array.from(new Map(brands.map((b) => [b.name.toLowerCase().trim(), b])).values())
                    .filter((b) => b.name.toLowerCase().trim() !== 'nova commerce')
                    .map((b) => (
                    <button
                      key={b.id}
                      onClick={() => {
                        selectBrandById(b.id);
                        setIsOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                        currentBrand?.id === b.id
                          ? 'bg-[#FBF5A5] font-bold text-[#111312]'
                          : 'hover:bg-[#F8F7F4] text-[#111312]'
                      }`}
                    >
                      <span className="truncate">{b.name}</span>
                      <span className="text-[10px] text-[#737478] capitalize">{b.verificationStatus}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Live API and DB Status */}
            <div className="pt-3 border-t border-[#EAE9E4] space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[#737478]">
                  <Server className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-medium">Backend API</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${dbConnected ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                  <span className="text-[11px] font-semibold text-[#111312]">
                    {dbConnected ? 'FastAPI Live' : 'Connecting...'}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[#737478]">
                  <Database className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-medium">Database</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${dbConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className={`text-[11px] font-semibold ${dbConnected ? 'text-emerald-700' : 'text-red-600'}`}>
                    {dbConnected ? (dbEngine === 'sqlite' ? 'SQLite (Local) Connected' : 'PostgreSQL Connected') : 'Disconnected'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
