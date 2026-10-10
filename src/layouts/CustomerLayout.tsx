import React from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DemoBadge } from '../components/ui/DemoBadge';
import { 
  Shield, 
  AlertTriangle, 
  ShieldCheck, 
  PhoneCall,
  CheckCircle2
} from 'lucide-react';

export const CustomerLayout: React.FC = () => {
  const { user } = useAuth();

  const navLinks = [
    { to: '/customer', label: 'Home', end: true },
    { to: '/customer/brands', label: 'Trusted Brands' },
    { to: '/customer/report', label: 'Submit Threat Report' },
    { to: '/customer/my-reports', label: 'My Reports' },
    { to: '/customer/reviews', label: 'Reviews & Feedback' },
    { to: '/customer/profile', label: 'My Profile' },
  ];

  return (
    <div className="min-h-screen bg-[#F8F7F4] text-[#111312] flex flex-col justify-between">
      {/* Top Banner: Solid Near-Black with Pale Butter Yellow Accent */}
      <div className="bg-[#111312] text-[#FBF5A5] text-xs py-2 px-4 text-center font-bold tracking-tight border-b border-[#2B2D2C]">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-[#FBF5A5]" />
          <span>So-cio Consumer Safety: Always verify official URLs before submitting credentials or card info.</span>
        </div>
      </div>

      {/* Main Navbar */}
      <header className="sticky top-0 z-40 bg-white border-b border-[#E2E1DC] px-4 sm:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          
          {/* Logo */}
          <Link to="/customer" className="flex items-center gap-3 group">
            <img
              src="/socio-logo.png"
              alt="So-cio Logo"
              className="w-10 h-10 object-contain shrink-0 group-hover:scale-105 transition-transform"
            />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-extrabold text-[#111312] tracking-tight">So-cio</span>
                <span className="text-[10px] font-bold text-[#111312] px-1.5 py-0.2 rounded-md bg-[#FBF5A5]">CUSTOMER</span>
              </div>
              <p className="text-[10px] text-[#737478] font-medium">Verified Consumer Protection</p>
            </div>
          </Link>

          {/* Segmented Nav Links Inspired by Image 2 */}
          <nav className="hidden md:flex items-center gap-1 bg-[#EFEFEA] p-1 rounded-xl border border-[#DCDAD4]">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-[#111312] text-[#FBF5A5] shadow-sm'
                      : 'text-[#434346] hover:text-[#111312] hover:bg-white/60'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          {/* Right Action Utilities */}
          <div className="flex items-center gap-3">
            <DemoBadge />

            {/* Quick Report CTA */}
            <Link
              to="/customer/report"
              className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#111312] hover:bg-[#232524] text-[#FBF5A5] border border-[#2B2D2C] text-xs font-bold transition-all shadow-sm"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-[#FBF5A5]" />
              <span>Report Scam</span>
            </Link>

            {/* User Phone Verified Indicator */}
            <Link
              to="/customer/profile"
              className="flex items-center gap-2 p-1.5 pr-2.5 rounded-xl bg-[#F4F3EF] border border-[#DCDAD4] text-xs text-[#111312] font-semibold hover:bg-[#EFEFEA] transition-colors"
            >
              <img
                src={user?.avatarUrl || 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=60&auto=format&fit=crop&q=80'}
                alt={user?.name}
                className="w-6 h-6 rounded-lg object-cover border border-[#D5D4CE]"
              />
              <span className="hidden sm:inline font-bold">{user?.name?.split(' ')[0] || 'Customer'}</span>
              {user?.isPhoneVerified && (
                <span title="Phone OTP Verified">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B]" />
                </span>
              )}
            </Link>
          </div>

        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

      {/* Customer Footer: Solid Near-Black High Contrast Section */}
      <footer className="bg-[#111312] text-white border-t border-[#2B2D2C] mt-12 py-10 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#FBF5A5] flex items-center justify-center text-[#111312]">
                <Shield className="w-4 h-4 fill-[#111312]" />
              </div>
              <span className="font-extrabold text-sm text-white tracking-tight">BrandShield AI</span>
            </div>
            <p className="text-xs text-[#9A9B9C] leading-relaxed">
              Empowering consumers with instant AI risk verification and direct threat takedown reporting for trusted brands.
            </p>
          </div>

          <div>
            <h5 className="text-xs font-bold text-[#FBF5A5] uppercase tracking-wider mb-3">Consumer Safety</h5>
            <ul className="space-y-2 text-xs text-[#9A9B9C]">
              <li><Link to="/customer/brands" className="hover:text-[#FBF5A5] transition-colors">Search Trusted Brands</Link></li>
              <li><Link to="/customer/report" className="hover:text-[#FBF5A5] transition-colors">Report Phishing Site</Link></li>
              <li><Link to="/customer/my-reports" className="hover:text-[#FBF5A5] transition-colors">Track Live Investigations</Link></li>
              <li><Link to="/customer/reviews" className="hover:text-[#FBF5A5] transition-colors">Read Brand Reviews</Link></li>
            </ul>
          </div>

          <div>
            <h5 className="text-xs font-bold text-[#FBF5A5] uppercase tracking-wider mb-3">For Organizations</h5>
            <ul className="space-y-2 text-xs text-[#9A9B9C]">
              <li><Link to="/auth/brand-login" className="hover:text-[#FBF5A5] transition-colors">Brand Owner Portal Login</Link></li>
              <li><Link to="/auth/brand-register" className="hover:text-[#FBF5A5] transition-colors">Register Official Brand</Link></li>
              <li><Link to="/brand-owner/brand-profile" className="hover:text-[#FBF5A5] transition-colors">DNS Domain Verification</Link></li>
              <li><Link to="/brand-owner/threat-overview" className="hover:text-[#FBF5A5] transition-colors">Automated Takedown API</Link></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h5 className="text-xs font-bold text-[#FBF5A5] uppercase tracking-wider">Cybersecurity Hotline</h5>
            <div className="p-3.5 rounded-xl bg-[#1C1E1D] border border-[#2D2F2E] text-xs">
              <div className="flex items-center gap-2 text-white font-bold mb-1">
                <PhoneCall className="w-3.5 h-3.5 text-[#FBF5A5]" />
                <span>24/7 Incident Triage</span>
              </div>
              <p className="text-[11px] text-[#9A9B9C] leading-snug">
                Fast-track takedown requests processed through ICANN-accredited registrar pipelines.
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto pt-8 mt-8 border-t border-[#262827] flex flex-col sm:flex-row items-center justify-between text-xs text-[#737478] gap-3">
          <div>&copy; 2026 So-cio &bull; ByteXL Hackathon Edition &bull; Editorial Design System</div>
          <div className="flex items-center gap-4">
            <span className="hover:text-[#FBF5A5] transition-colors cursor-pointer">Security Standards</span>
            <span>&bull;</span>
            <span className="hover:text-[#FBF5A5] transition-colors cursor-pointer">API Docs</span>
            <span>&bull;</span>
            <span className="hover:text-[#FBF5A5] transition-colors cursor-pointer">Responsible Disclosure</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
