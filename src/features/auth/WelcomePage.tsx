import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Mascot } from '../../components/ui/Mascot';
import { DemoBadge } from '../../components/ui/DemoBadge';
import { Shield, Building2, User, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';

export const WelcomePage: React.FC = () => {
  const { switchRole } = useAuth();
  const navigate = useNavigate();

  const handleSelectRole = (role: 'brand_owner' | 'customer', targetPath: string) => {
    switchRole(role);
    navigate(targetPath);
  };

  return (
    <div className="min-h-screen bg-[#F8F7F4] text-[#111312] p-4 sm:p-6 lg:p-10 flex flex-col justify-between relative">
      {/* Top Bar */}
      <header className="max-w-7xl w-full mx-auto flex items-center justify-between z-20">
        <Link to="/" className="flex items-center gap-3">
          <img
            src="/socio-logo.png"
            alt="So-cio Logo"
            className="w-10 h-10 object-contain shrink-0"
          />
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-extrabold text-[#111312] tracking-tight">So-cio</span>
            </div>
            <p className="text-[10px] text-[#737478] font-medium">Digital Risk & Impersonation Protection</p>
          </div>
        </Link>

        <DemoBadge />
      </header>

      {/* Center Welcome Section */}
      <main className="max-w-5xl w-full mx-auto my-auto py-8 z-10 text-center">
        {/* Pill Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#111312] border border-[#2B2D2C] shadow-sm text-xs font-bold text-[#FBF5A5] mb-4">
          <Sparkles className="w-3.5 h-3.5 text-[#FBF5A5]" />
          <span>EDITORIAL CYBERSECURITY &bull; DIGITAL PERIMETER</span>
        </div>

        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-[#111312] tracking-tight leading-tight max-w-3xl mx-auto">
          Protect Your Brand Identity.<br />
          <span className="inline-block mt-2 px-3.5 py-1 rounded-2xl bg-[#111312] text-[#FBF5A5] border border-[#2B2D2C]">
            Empower Your Customers.
          </span>
        </h1>

        <p className="text-sm sm:text-base text-[#434346] max-w-2xl mx-auto mt-4 leading-relaxed font-normal">
          The all-in-one AI platform detecting spoofed domains, rogue apps, social impersonators, and fraudulent campaigns in real-time.
        </p>

        {/* Mascot Center Stage */}
        <div className="my-6 flex justify-center">
          <Mascot pose="guarding" size="xl" />
        </div>

        {/* Two Experience Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto text-left">
          
          {/* Card 1: Brand Owner Portal (Solid Near-Black Card) */}
          <div className="bg-[#111312] text-white rounded-3xl p-6 sm:p-8 border border-[#2B2D2C] shadow-2xl flex flex-col justify-between group">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#FBF5A5] text-[#111312] flex items-center justify-center group-hover:scale-105 transition-transform shadow-sm">
                <Building2 className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-[#FBF5A5] uppercase tracking-wider">For Organizations</span>
                <h3 className="text-xl font-extrabold text-white mt-0.5">Brand Owner Portal</h3>
                <p className="text-xs text-[#9A9B9C] mt-2 leading-relaxed">
                  Monitor registered domains, analyze AI risk evidence, automate abuse takedowns, and manage official brand channels.
                </p>
              </div>

              <div className="space-y-2 pt-2 text-xs text-[#D6D6D8] font-medium">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#FBF5A5] shrink-0" />
                  <span>Sub-minute domain typosquatting alerts</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#FBF5A5] shrink-0" />
                  <span>AI evidence locker & registrar takedown desk</span>
                </div>
              </div>
            </div>

            <div className="pt-6 mt-4 border-t border-[#262827] flex items-center gap-3">
              <button
                onClick={() => handleSelectRole('brand_owner', '/brand-owner/overview')}
                className="flex-1 py-3 px-4 rounded-xl bg-[#FBF5A5] hover:bg-[#F6EF8A] text-[#111312] text-xs font-bold shadow-sm flex items-center justify-center gap-2 group-hover:gap-3 transition-all"
              >
                <span>Enter Brand Portal</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => handleSelectRole('brand_owner', '/auth/brand-register')}
                className="py-3 px-4 rounded-xl bg-[#1C1E1D] hover:bg-[#252726] text-white text-xs font-semibold border border-[#2D2F2E] transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>

          {/* Card 2: Customer Portal (Solid White Card) */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#D5D4CE] shadow-sm flex flex-col justify-between group">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center group-hover:scale-105 transition-transform shadow-sm">
                <User className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-[#434346] uppercase tracking-wider">For Consumers</span>
                <h3 className="text-xl font-extrabold text-[#111312] mt-0.5">Customer Portal</h3>
                <p className="text-xs text-[#737478] mt-2 leading-relaxed">
                  Verify authentic brand channels, submit suspicious phishing links or scam SMS, and track live security investigations.
                </p>
              </div>

              <div className="space-y-2 pt-2 text-xs text-[#111312] font-semibold">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                  <span>Instant URL & domain security checker</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                  <span>Phone-verified scam reporting & status tracker</span>
                </div>
              </div>
            </div>

            <div className="pt-6 mt-4 border-t border-[#EAE9E4] flex items-center gap-3">
              <button
                onClick={() => handleSelectRole('customer', '/customer')}
                className="flex-1 py-3 px-4 rounded-xl bg-[#111312] hover:bg-[#232524] text-[#FBF5A5] text-xs font-bold flex items-center justify-center gap-2 group-hover:gap-3 transition-all"
              >
                <span>Enter as Consumer</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <Link
                to="/auth/customer-signin"
                className="py-3 px-4 rounded-xl bg-[#F4F3EF] hover:bg-[#EFEFEA] text-[#111312] text-xs font-semibold border border-[#D5D4CE]"
              >
                Sign In
              </Link>
            </div>
          </div>

        </div>
      </main>

      {/* Bottom info */}
      <footer className="max-w-7xl w-full mx-auto py-3 text-center text-xs text-[#737478] z-10 border-t border-[#E2E1DC]">
        So-cio &bull; Editorial Design System &bull; ByteXL Hackathon
      </footer>
    </div>
  );
};
