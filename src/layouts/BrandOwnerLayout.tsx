import React, { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useBrand } from '../context/BrandContext';
import { DemoBadge } from '../components/ui/DemoBadge';
import { 
  Shield, 
  LayoutDashboard, 
  ShieldAlert, 
  Globe2, 
  Crosshair, 
  Workflow,
  Bell, 
  TrendingUp,
  Lightbulb,
  Sparkles,
  FileText, 
  Building2,
  ChevronDown, 
  ChevronLeft,
  ChevronRight,
  Home,
  Archive,
  Search, 
  LogOut, 
  Menu, 
  X, 
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Eye,
  MessageSquareHeart
} from 'lucide-react';

export const BrandOwnerLayout: React.FC = () => {
  const { user, signOut } = useAuth();
  const { brands, currentBrand, selectBrandById } = useBrand();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isBrandSelectorOpen, setIsBrandSelectorOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/brand-owner/threat-management?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  // Exactly 13 Core Required User-Facing Features
  const navItems = [
    { to: '/brand-owner/dashboard', label: '1. Dashboard', icon: LayoutDashboard },
    { to: '/brand-owner/threat-overview', label: '2. Threat Overview', icon: Globe2 },
    { to: '/brand-owner/threat-management', label: '3. Threat Management', icon: ShieldAlert, badge: '4' },
    { to: '/brand-owner/threat-details', label: '4. Threat Details', icon: Eye },
    { to: '/brand-owner/campaign-overview', label: '5. Campaign Overview', icon: Crosshair },
    { to: '/brand-owner/campaign-details', label: '6. Campaign Details', icon: Workflow },
    { to: '/brand-owner/alerts', label: '7. Alerts', icon: Bell, badge: '3' },
    { to: '/brand-owner/risk-trends', label: '8. Risk Trends', icon: TrendingUp },
    { to: '/brand-owner/recommended-actions', label: '9. Recommended Actions', icon: Lightbulb },
    { to: '/brand-owner/ai-threat-explanation', label: '10. Why is this a threat?', icon: Sparkles },
    { to: '/brand-owner/reports', label: '11. Reports', icon: FileText },
    { to: '/brand-owner/brand-profile', label: '12. Brand Profile & Settings', icon: Building2 },
    { to: '/brand-owner/reviews', label: '13. Customer Reviews', icon: MessageSquareHeart },
  ];

  return (
    <div className="min-h-screen bg-[#F8F7F4] flex text-[#111312]">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-[#111312]/80 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar: Solid Near-Black with Editorial Luxury Accents */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 bg-[#111312] border-r border-[#262827] flex flex-col justify-between transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } ${
          isCollapsed ? 'w-64 lg:w-20' : 'w-64 lg:w-64'
        }`}
      >
        {/* Circular Animated Collapse/Expand Toggle Button (Image 1 reference) */}
        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="hidden lg:flex absolute -right-3.5 top-6 z-50 w-7 h-7 rounded-full bg-[#181A19] border border-[#2D2F2E] text-[#9A9B9C] hover:text-[#FBF5A5] hover:border-[#FBF5A5]/60 hover:bg-[#222423] items-center justify-center shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#FBF5A5]/40 cursor-pointer"
        >
          {isCollapsed ? (
            <ChevronRight className="w-3.5 h-3.5 text-[#FBF5A5]" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5" />
          )}
        </button>

        {/* So-cio Header Logo */}
        <div>
          <div className={`border-b border-[#242625] flex items-center transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            isCollapsed ? 'p-4 lg:justify-center' : 'p-4 sm:p-5 justify-between'
          }`}>
            <Link to="/brand-owner/overview" className="flex items-center gap-2.5 min-w-0" title="So-cio - Brand Security Portal">
              <img
                src="/socio-logo.png"
                alt="So-cio Logo"
                className="w-9 h-9 object-contain shrink-0 drop-shadow-sm"
              />
              <div className={`overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                isCollapsed ? 'w-0 opacity-0 hidden lg:hidden' : 'w-auto opacity-100 block'
              }`}>
                <div className="flex items-center gap-1.5 whitespace-nowrap">
                  <span className="text-lg font-extrabold text-white tracking-tight">So-cio</span>
                </div>
                <p className="text-[10px] text-[#9A9B9C] font-medium tracking-wide whitespace-nowrap">Brand Security Portal</p>
              </div>
            </Link>

            <button
              onClick={() => setIsSidebarOpen(false)}
              className="lg:hidden p-1.5 rounded-lg text-[#9A9B9C] hover:text-white hover:bg-[#1E201F]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Active Brand Switcher Pill */}
          <div className={`border-b border-[#242625] relative transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            isCollapsed ? 'p-2 flex justify-center' : 'p-3'
          }`}>
            <button
              onClick={() => setIsBrandSelectorOpen(!isBrandSelectorOpen)}
              title={currentBrand?.name || 'ApexBank Global'}
              className={`w-full rounded-xl bg-[#181A19] hover:bg-[#202221] border border-[#2D2F2E] flex items-center transition-all group ${
                isCollapsed ? 'p-2 lg:w-11 lg:h-11 justify-center' : 'p-2.5 justify-between'
              }`}
            >
              <div className={`flex items-center min-w-0 ${isCollapsed ? 'justify-center' : 'gap-2.5'}`}>
                <img
                  src={currentBrand?.logoUrl || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=60&auto=format&fit=crop&q=80'}
                  alt={currentBrand?.name}
                  className="w-7 h-7 rounded-lg object-cover border border-[#3A3C3B] shrink-0"
                />
                <div className={`text-left min-w-0 overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                  isCollapsed ? 'w-0 opacity-0 hidden lg:hidden' : 'w-auto opacity-100 block'
                }`}>
                  <div className="text-xs font-bold text-white truncate whitespace-nowrap">{currentBrand?.name || 'ApexBank'}</div>
                  <div className="flex items-center gap-1 text-[10px] text-[#9A9B9C] whitespace-nowrap">
                    {currentBrand?.verificationStatus === 'verified' ? (
                      <span className="text-[#FBF5A5] flex items-center gap-0.5 font-medium">
                        <CheckCircle2 className="w-2.5 h-2.5" /> Verified Brand
                      </span>
                    ) : (
                      <span className="text-amber-400 flex items-center gap-0.5 font-medium">
                        <AlertTriangle className="w-2.5 h-2.5" /> Pending DNS
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <ChevronDown className={`w-4 h-4 text-[#9A9B9C] group-hover:text-[#FBF5A5] shrink-0 transition-transform ${
                isCollapsed ? 'hidden lg:hidden' : 'block'
              }`} />
            </button>

            {/* Brand Dropdown Menu */}
            {isBrandSelectorOpen && (
              <>
                <div className="fixed inset-0 z-20" onClick={() => setIsBrandSelectorOpen(false)} />
                <div className={`absolute ${
                  isCollapsed ? 'left-full top-0 ml-2 w-56' : 'left-3 right-3 mt-1.5'
                } bg-[#181A19] rounded-2xl border border-[#2D2F2E] shadow-2xl p-2 z-50 space-y-1`}>
                  <div className="text-[10px] font-bold text-[#737478] px-2 py-1 uppercase tracking-wider">Switch Brand</div>
                  {Array.from(new Map(brands.map((b) => [b.name.toLowerCase().trim(), b])).values())
                    .filter((b) => {
                      const name = b.name.toLowerCase().trim();
                      return name !== 'nova commerce' && name !== 'lumina cloud' && name !== 'aurapay checkout';
                    })
                    .map((b) => (
                    <button
                      key={b.id}
                      onClick={() => {
                        selectBrandById(b.id);
                        setIsBrandSelectorOpen(false);
                      }}
                      className={`w-full flex items-center justify-between p-2 rounded-xl text-xs transition-colors ${
                        currentBrand?.id === b.id
                          ? 'bg-[#FBF5A5] text-[#111312] font-bold'
                          : 'hover:bg-[#222423] text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <img src={b.logoUrl} className="w-5 h-5 rounded-md object-cover" />
                        <span className="truncate">{b.name}</span>
                      </div>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                        currentBrand?.id === b.id ? 'bg-[#111312] text-[#FBF5A5]' : 'bg-[#2B2D2C] text-[#D6D6D8]'
                      }`}>
                        {b.verificationStatus}
                      </span>
                    </button>
                  ))}
                  
                  <Link
                    to="/auth/brand-register"
                    onClick={() => setIsBrandSelectorOpen(false)}
                    className="flex items-center gap-2 p-2 text-xs font-semibold text-[#FBF5A5] hover:bg-[#222423] rounded-xl pt-2 border-t border-[#2D2F2E]"
                  >
                    <Building2 className="w-4 h-4" />
                    <span>+ Register New Brand</span>
                  </Link>
                </div>
              </>
            )}
          </div>

          {/* Navigation Links: High Contrast Editorial Hierarchy */}
          <nav className={`space-y-1 max-h-[calc(100vh-270px)] overflow-y-auto transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            isCollapsed ? 'p-2' : 'p-3'
          }`}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.to);

              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setIsSidebarOpen(false)}
                  className={`relative flex items-center rounded-xl text-xs font-semibold transition-all duration-150 group ${
                    isCollapsed ? 'lg:justify-center lg:p-2.5' : 'justify-between px-3.5 py-2.5'
                  } ${
                    isActive
                      ? 'bg-[#FBF5A5] text-[#111312] shadow-sm font-bold'
                      : 'text-[#9A9B9C] hover:text-white hover:bg-[#1C1E1D]'
                  }`}
                >
                  <div className={`flex items-center min-w-0 ${isCollapsed ? 'lg:justify-center' : 'gap-3'}`}>
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#111312]' : 'text-[#737478]'}`} />
                    <span className={`overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] whitespace-nowrap ${
                      isCollapsed ? 'w-0 opacity-0 hidden lg:hidden' : 'w-auto opacity-100 block'
                    }`}>
                      {item.label}
                    </span>
                  </div>

                  {item.badge && (
                    <>
                      {/* Expanded state badge */}
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold whitespace-nowrap ${
                        isActive ? 'bg-[#111312] text-[#FBF5A5]' : 'bg-[#434346] text-[#FBF5A5]'
                      } ${isCollapsed ? 'hidden lg:hidden' : 'inline'}`}>
                        {item.badge}
                      </span>

                      {/* Collapsed state badge indicator */}
                      {isCollapsed && (
                        <span className={`hidden lg:flex absolute top-1 right-1 w-4 h-4 rounded-full text-[9px] font-bold items-center justify-center shadow-sm ${
                          isActive ? 'bg-[#111312] text-[#FBF5A5]' : 'bg-[#434346] text-[#FBF5A5]'
                        }`}>
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}

                  {/* Floating Tooltip in Collapsed Rail Mode */}
                  {isCollapsed && (
                    <div className="hidden lg:group-hover:flex absolute left-full ml-3 px-2.5 py-1.5 rounded-xl bg-[#181A19] text-white text-xs font-semibold border border-[#2D2F2E] shadow-2xl items-center gap-1.5 whitespace-nowrap pointer-events-none z-50">
                      <span>{item.label}</span>
                      {item.badge && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-[#434346] text-[#FBF5A5] font-bold">
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Bottom: Protection Status */}
        <div className={`border-t border-[#242625] bg-[#141615] transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] overflow-hidden ${
          isCollapsed ? 'h-0 p-0 border-t-0 opacity-0' : 'p-3.5 opacity-100'
        }`}>
          <div className="p-3 rounded-xl bg-[#1C1E1D] border border-[#2D2F2E] text-xs">
            <div className="flex items-center justify-between font-bold text-white mb-1">
              <span className="flex items-center gap-1.5 whitespace-nowrap">
                <Sparkles className="w-3.5 h-3.5 text-[#FBF5A5]" />
                Perimeter Defense
              </span>
              <span className="text-[11px] text-[#FBF5A5] font-extrabold">99.8%</span>
            </div>
            <p className="text-[11px] text-[#9A9B9C] leading-snug">
              Autonomous crawler analyzing 40k+ TLD variations/hr.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Workspace */}
      <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
        isCollapsed ? 'lg:pl-20' : 'lg:pl-64'
      }`}>
        {/* Top Header: Clean Solid Editorial Surface */}
        <header className="sticky top-0 z-30 bg-white border-b border-[#E2E1DC] px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
            {/* Mobile Sidebar Hamburger */}
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl text-[#737478] hover:text-[#111312] hover:bg-[#F4F3EF]"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Navigation History Chevrons (Back / Forward) */}
            <div className="hidden xl:flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={() => navigate(-1)}
                title="Go back"
                className="w-8 h-8 rounded-full bg-[#F4F3EF] hover:bg-[#EAE8E3] text-[#434346] hover:text-[#111312] border border-[#DCDAD4] flex items-center justify-center transition-all duration-150 active:scale-95 shadow-xs"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => navigate(1)}
                title="Go forward"
                className="w-8 h-8 rounded-full bg-[#F4F3EF] hover:bg-[#EAE8E3] text-[#434346] hover:text-[#111312] border border-[#DCDAD4] flex items-center justify-center transition-all duration-150 active:scale-95 shadow-xs"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Circular Home Button (Image 2 aesthetic) */}
            <Link
              to="/brand-owner/dashboard"
              title="Dashboard Home"
              className="hidden sm:flex w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#111312] hover:bg-[#181A19] border border-[#2D2F2E] text-white hover:text-[#FBF5A5] items-center justify-center shadow-sm transition-all duration-200 hover:scale-105 active:scale-95 shrink-0 group"
            >
              <Home className="w-4 h-4 text-white group-hover:text-[#FBF5A5] transition-colors" />
            </Link>

            {/* Pill-Shaped Aesthetic Search Bar (Image 2 aesthetic on BrandShield theme) */}
            <form onSubmit={handleSearchSubmit} className="relative group w-64 sm:w-80 md:w-96 lg:w-[420px] transition-all">
              <div className="flex items-center h-10 px-3.5 rounded-full bg-[#111312] hover:bg-[#181A19] border border-[#2D2F2E] hover:border-[#434346] focus-within:border-[#FBF5A5] focus-within:ring-2 focus-within:ring-[#FBF5A5]/25 shadow-sm transition-all duration-200">
                {/* Search Magnifying Glass Icon */}
                <Search className="w-4 h-4 text-[#9A9B9C] group-focus-within:text-[#FBF5A5] transition-colors shrink-0 mr-2.5" />
                
                {/* Search Input */}
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search website, evidence, account name, ticket..."
                  className="w-full bg-transparent text-xs sm:text-sm font-medium text-white placeholder:text-[#8E9091] focus:outline-none truncate"
                />

                {/* Keyboard Shortcut Hint */}
                <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono font-bold text-[#8E9091] group-focus-within:text-[#FBF5A5] bg-[#222423] rounded-md border border-[#363837] shrink-0 mx-1">
                  ⌘K
                </kbd>

                {/* Vertical Divider (Image 2 aesthetic) */}
                <div className="h-4 w-px bg-[#363837] mx-1.5 shrink-0" />

                {/* Right Browse / Threat Index Icon (Image 2 aesthetic) */}
                <button
                  type="button"
                  onClick={() => navigate('/brand-owner/threat-overview')}
                  title="Browse Threat Intelligence Index"
                  className="p-1 rounded-full text-[#9A9B9C] hover:text-[#FBF5A5] hover:bg-[#222423] transition-colors shrink-0 cursor-pointer"
                >
                  <Archive className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>

          {/* Right Header Utilities */}
          <div className="flex items-center gap-3">
            <DemoBadge />

            {/* Notification Bell */}
            <Link
              to="/brand-owner/alerts"
              className="relative p-2.5 rounded-xl bg-[#F4F3EF] hover:bg-[#EFEFEA] border border-[#DCDAD4] text-[#434346] hover:text-[#111312] transition-colors"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#111312] ring-2 ring-[#FBF5A5]" />
            </Link>

            {/* User Profile Avatar & Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                className="flex items-center gap-2 p-1.5 pr-2.5 rounded-xl hover:bg-[#F4F3EF] border border-transparent hover:border-[#DCDAD4] transition-all"
              >
                <img
                  src={user?.avatarUrl || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&auto=format&fit=crop&q=80'}
                  alt={user?.name}
                  className="w-8 h-8 rounded-lg object-cover border border-[#D5D4CE]"
                />
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-bold text-[#111312] leading-tight">{user?.name || 'Elena Rostova'}</div>
                  <div className="text-[10px] text-[#737478] capitalize">Brand Security Lead</div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-[#737478]" />
              </button>

              {isProfileMenuOpen && (
                <>
                  <div className="fixed inset-0 z-20" onClick={() => setIsProfileMenuOpen(false)} />
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl border border-[#D5D4CE] shadow-2xl p-3 z-30 space-y-1">
                    <div className="px-3 py-2 border-b border-[#EAE9E4]">
                      <p className="text-xs font-bold text-[#111312]">{user?.name}</p>
                      <p className="text-[11px] text-[#737478] truncate">{user?.email}</p>
                    </div>

                    <Link
                      to="/customer"
                      onClick={() => setIsProfileMenuOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-[#111312] hover:bg-[#F8F7F4] rounded-lg"
                    >
                      <ExternalLink className="w-4 h-4 text-[#434346]" />
                      <span>Switch to Customer Portal</span>
                    </Link>

                    <Link
                      to="/brand-owner/brand-profile"
                      onClick={() => setIsProfileMenuOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-[#111312] hover:bg-[#F8F7F4] rounded-lg"
                    >
                      <Building2 className="w-4 h-4 text-[#737478]" />
                      <span>Brand Profile & Settings</span>
                    </Link>

                    <button
                      onClick={() => {
                        signOut();
                        setIsProfileMenuOpen(false);
                        navigate('/auth');
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-50 rounded-lg pt-2 border-t border-[#EAE9E4]"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Dynamic Page Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
