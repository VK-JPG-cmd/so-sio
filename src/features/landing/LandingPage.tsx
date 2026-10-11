import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldMascotScene } from '../../components/3d/ShieldMascotScene';
import { DemoBadge } from '../../components/ui/DemoBadge';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';
import { useNotification } from '../../context/NotificationContext';
import { 
  Shield, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  Globe2, 
  Users2, 
  Crosshair, 
  Fingerprint, 
  Search, 
  Send, 
  Layers, 
  ShieldCheck, 
  Building2, 
  User, 
  Cpu
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { switchRole } = useAuth();
  const { showToast } = useNotification();
  const navigate = useNavigate();

  // Cinematic Intro State
  const [showIntro, setShowIntro] = useState(true);

  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (e.data && (e.data.type === 'SOCIO_INTRO_COMPLETE' || e.data.type === 'SOCIO_INTRO_SKIP')) {
        setShowIntro(false);
      }
    };
    window.addEventListener('message', handleMessage);

    // Auto-transition to main page after 7.4 seconds
    const autoTimer = setTimeout(() => {
      setShowIntro(false);
    }, 7400);

    return () => {
      window.removeEventListener('message', handleMessage);
      clearTimeout(autoTimer);
    };
  }, []);



  const handleSelectRoleAndNavigate = (role: 'brand_owner' | 'customer', path: string) => {
    switchRole(role);
    navigate(path);
  };

  return (
    <div className="relative min-h-screen bg-[#F8F7F4] text-[#111312] font-sans antialiased selection:bg-[#FBF5A5] selection:text-[#111312] overflow-x-hidden">
      
      {/* 1. CINEMATIC INTRO OVERLAY (Pure video animation — Image 3 controls removed) */}
      <AnimatePresence>
        {showIntro && (
          <motion.div
            key="cinematic-logo-intro"
            initial={{ opacity: 1 }}
            exit={{ 
              opacity: 0, 
              scale: 1.04, 
              filter: 'blur(10px)',
              transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] } 
            }}
            className="fixed inset-0 z-50 bg-[#111312] overflow-hidden"
          >
            <iframe
              src="/landing.html"
              title="So-cio — Premium Cinematic Logo Reveal"
              className="w-full h-full border-0 block"
              allow="autoplay; fullscreen"
            />

            {/* Discreet Skip Intro pill in bottom-right corner */}
            <div className="absolute bottom-6 right-6 z-30 pointer-events-auto">
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.2, duration: 0.6 }}
                onClick={() => setShowIntro(false)}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#111312]/85 hover:bg-[#1C1E1D] text-xs font-semibold text-[#9A9B9C] hover:text-[#FBF5A5] border border-white/10 hover:border-[#FBF5A5]/40 backdrop-blur-md transition-all shadow-xl group cursor-pointer"
              >
                <span>Skip Intro</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. MAIN BRANDSHIELD LANDING PAGE (Image 2 — Opens with smooth transition) */}
      <motion.div
        key="main-landing-content"
        initial={showIntro ? { opacity: 0, y: 15 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="w-full min-h-screen"
      >
        {/* Header Navigation: Solid Near-Black High-End Bar */}
        <header className="sticky top-0 z-50 bg-[#111312] border-b border-[#2B2D2C] px-4 sm:px-8 py-3.5 shadow-md">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
            
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <img
                src="/socio-logo.png"
                alt="So-cio Logo"
                className="w-10 h-10 object-contain shrink-0 group-hover:scale-105 transition-transform"
              />
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-extrabold text-white tracking-tight">So-cio</span>
                </div>
                <p className="text-[10px] text-[#9A9B9C] font-medium">Digital Risk & Impersonation Protection</p>
              </div>
            </Link>

            {/* Center Nav Links */}
            <nav className="hidden lg:flex items-center gap-7 text-xs font-semibold text-[#9A9B9C]">
              <a href="#capabilities" className="hover:text-[#FBF5A5] transition-colors">Capabilities</a>
              <a href="#how-it-works" className="hover:text-[#FBF5A5] transition-colors">How It Works</a>
              <a href="#explainable-ai" className="hover:text-[#FBF5A5] transition-colors">Explainable AI</a>
              <a href="#portals" className="hover:text-[#FBF5A5] transition-colors">Portals</a>
            </nav>

            {/* Right Utilities */}
            <div className="flex items-center gap-3">
              <DemoBadge />

              <button
                onClick={() => handleSelectRoleAndNavigate('brand_owner', '/auth/brand-register')}
                className="hidden sm:inline-flex text-xs font-bold text-[#9A9B9C] hover:text-[#FBF5A5] px-3 py-1.5 rounded-lg transition-colors"
              >
                Sign In
              </button>

              <Link
                to="/auth/brand-register"
                className="px-4 py-2 rounded-xl bg-[#FBF5A5] hover:bg-[#F6EF8A] text-[#111312] text-xs font-bold shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                Protect Your Brand
              </Link>
            </div>

          </div>
        </header>

      {/* SECTION A: THE HERO SECTION */}
      <section className="relative pt-12 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
        
        {/* Hero Badge */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#111312] border border-[#2B2D2C] shadow-sm text-xs font-bold text-[#FBF5A5] mb-6"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#FBF5A5]" />
          <span>EDITORIAL SECURITY &bull; DIGITAL RISK DEFENSE</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-[#111312] tracking-tight leading-[1.1] max-w-4xl"
        >
          Protect Your Brand Identity.<br />
          <span className="inline-block mt-2 px-3.5 py-1 rounded-2xl bg-[#111312] text-[#FBF5A5] border border-[#2B2D2C]">
            Empower Your Customers.
          </span>
        </motion.h1>

        {/* Supporting Text */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-sm sm:text-base text-[#434346] max-w-2xl mt-6 leading-relaxed font-normal"
        >
          Discover suspicious domains, detect executive impersonation, and investigate digital threats with explainable AI and autonomous registrar pipelines.
        </motion.p>

        {/* Action CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center gap-3.5 mt-8 z-20"
        >
          <button
            onClick={() => handleSelectRoleAndNavigate('brand_owner', '/auth/brand-register')}
            className="w-full sm:w-auto px-7 py-3 rounded-xl bg-[#111312] hover:bg-[#232524] text-[#FBF5A5] text-sm font-bold shadow-sm flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] border border-[#2B2D2C]"
          >
            <span>Protect Your Brand</span>
            <ArrowRight className="w-4 h-4 text-[#FBF5A5]" />
          </button>

          <a
            href="#capabilities"
            className="w-full sm:w-auto px-7 py-3 rounded-xl bg-white hover:bg-[#F4F3EF] text-[#111312] text-sm font-bold border border-[#D5D4CE] shadow-sm transition-all"
          >
            Explore the Platform
          </a>
        </motion.div>

        {/* Interactive Action Pills Inspired by Image 2 Tags */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="flex flex-wrap items-center justify-center gap-2 mt-6 max-w-3xl z-20"
        >
          <a
            href="#demo-sandbox"
            className="inline-flex items-center justify-center bg-[#222423] text-[#D6D6D8] border border-[#363837] rounded-full text-xs font-semibold px-4 py-1.5 shadow-sm hover:bg-[#FBF5A5] hover:text-[#111312] transition-all cursor-pointer"
          >
            Scan Candidate Domain
          </a>
          <a
            href="#capabilities"
            className="inline-flex items-center justify-center bg-[#222423] text-[#D6D6D8] border border-[#363837] rounded-full text-xs font-semibold px-4 py-1.5 shadow-sm hover:bg-[#FBF5A5] hover:text-[#111312] transition-all cursor-pointer"
          >
            Impersonation Radar
          </a>
          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center bg-[#222423] text-[#D6D6D8] border border-[#363837] rounded-full text-xs font-semibold px-4 py-1.5 shadow-sm hover:bg-[#FBF5A5] hover:text-[#111312] transition-all cursor-pointer"
          >
            Autonomous Takedowns
          </a>
          <Link
            to="/customer"
            className="inline-flex items-center justify-center bg-[#222423] text-[#D6D6D8] border border-[#363837] rounded-full text-xs font-semibold px-4 py-1.5 shadow-sm hover:bg-[#FBF5A5] hover:text-[#111312] transition-all cursor-pointer"
          >
            Customer Safety Portal
          </Link>
          <button
            type="button"
            onClick={() => {
              navigator.clipboard.writeText('security@brandshield.ai');
              showToast({ type: 'success', title: 'Copied', message: 'Security desk email copied to clipboard.' });
            }}
            className="inline-flex items-center justify-center bg-[#FBF5A5] text-[#111312] border border-[#FBF5A5] rounded-full text-xs font-bold px-4 py-1.5 shadow-sm hover:bg-[#F6EF8A] transition-all cursor-pointer gap-1.5"
          >
            <span>Reach SOC: <span className="underline">security@brandshield.ai</span></span>
            <span className="text-[10px]">📋</span>
          </button>
        </motion.div>

        {/* Trust Caption */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-xs text-[#737478] mt-4 tracking-wide font-medium flex items-center gap-2"
        >
          <ShieldCheck className="w-4 h-4 text-[#2F7C5B]" />
          <span>Evidence-led detection &bull; Explainable risk insights &bull; Human-reviewed decisions.</span>
        </motion.p>

        {/* 3D Living Mascot Centerpiece ("Shielly — AI Assistant") */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.35, ease: "easeOut" }}
          className="my-4 sm:my-6 relative flex items-center justify-center"
        >
          <ShieldMascotScene
            pose="guarding"
            scale={1.2}
            className="w-80 h-80 sm:w-[420px] sm:h-[420px]"
            interactive={true}
          />
        </motion.div>

        {/* Quick Micro-Metrics Bar: Solid Near-Black Card Inspired by Image 2 Stats */}
        <div className="w-full max-w-4xl grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-3xl bg-[#111312] border border-[#2B2D2C] shadow-2xl text-left text-white">
          <div className="p-3">
            <p className="text-[10px] font-bold text-[#FBF5A5] uppercase tracking-wider">Typosquat Scan</p>
            <p className="text-xl font-extrabold text-white mt-0.5">450+ TLDs</p>
            <p className="text-[10px] text-[#9A9B9C]">Sub-minute ingestion</p>
          </div>
          <div className="p-3 border-l border-[#262827]">
            <p className="text-[10px] font-bold text-[#FBF5A5] uppercase tracking-wider">AI Confidence</p>
            <p className="text-xl font-extrabold text-white mt-0.5">99.4%</p>
            <p className="text-[10px] text-[#9A9B9C]">Perceptual hash verified</p>
          </div>
          <div className="p-3 border-l border-[#262827]">
            <p className="text-[10px] font-bold text-[#FBF5A5] uppercase tracking-wider">Avg. Takedown</p>
            <p className="text-xl font-extrabold text-[#FBF5A5] mt-0.5">&lt; 4.2 Hours</p>
            <p className="text-[10px] text-[#9A9B9C]">Direct abuse pipeline</p>
          </div>
          <div className="p-3 border-l border-[#262827]">
            <p className="text-[10px] font-bold text-[#FBF5A5] uppercase tracking-wider">Consumer Trust</p>
            <p className="text-xl font-extrabold text-white mt-0.5">Phone Verified</p>
            <p className="text-[10px] text-[#9A9B9C]">Crowdsourced safety</p>
          </div>
        </div>

      </section>

      {/* SECTION B: PRODUCT CAPABILITIES */}
      <section id="capabilities" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold text-[#434346] uppercase tracking-wider bg-[#EFEFEA] px-3 py-1 rounded-full border border-[#DCDAD4]">
            Enterprise Defense Perimeter
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#111312] tracking-tight">
            Intelligent Threat Radar
          </h2>
          <p className="text-xs sm:text-sm text-[#434346] leading-relaxed">
            Multi-vector digital risk defense powered by perceptual image hashing, natural language urgency modeling, and automated registrar orchestration.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card 1: Impersonation Detection */}
          <Card
            hoverEffect
            className="p-8 space-y-5 bg-white border border-[#E2E1DC] shadow-sm rounded-3xl group"
          >
            <div className="w-13 h-13 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center border border-[#2B2D2C] group-hover:scale-105 transition-transform shadow-sm">
              <Users2 className="w-6 h-6" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-[#111312]">Impersonation Detection</h3>
              <p className="text-xs text-[#737478] leading-relaxed">
                Scan social networks (X, Telegram, LinkedIn, Instagram, Discord) for fake customer support handles, scam investment bots, and unauthorized executive profiles.
              </p>
            </div>

            <div className="pt-2 space-y-2 text-xs text-[#111312] font-semibold">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                <span>Real-time brand mention scraping</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                <span>VIP fast-track social platform takedowns</span>
              </div>
            </div>
          </Card>

          {/* Card 2: Suspicious Website Analysis */}
          <Card
            hoverEffect
            className="p-8 space-y-5 bg-white border border-[#E2E1DC] shadow-sm rounded-3xl group"
          >
            <div className="w-13 h-13 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center border border-[#2B2D2C] group-hover:scale-105 transition-transform shadow-sm">
              <Globe2 className="w-6 h-6" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-[#111312]">Suspicious Website Analysis</h3>
              <p className="text-xs text-[#737478] leading-relaxed">
                Autonomous crawler querying 450+ global TLDs for lookalikes, homoglyphs, and cloned login portals intercepting customer banking or SaaS credentials.
              </p>
            </div>

            <div className="pt-2 space-y-2 text-xs text-[#111312] font-semibold">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                <span>Pixel-level SVG & logo match hashing</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                <span>DOM diffing to external C2 exfiltration</span>
              </div>
            </div>
          </Card>

          {/* Card 3: Threat Intelligence & Campaign Correlation */}
          <Card
            hoverEffect
            className="p-8 space-y-5 bg-white border border-[#E2E1DC] shadow-sm rounded-3xl group"
          >
            <div className="w-13 h-13 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center border border-[#2B2D2C] group-hover:scale-105 transition-transform shadow-sm">
              <Crosshair className="w-6 h-6" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-[#111312]">Threat Campaigns & IOCs</h3>
              <p className="text-xs text-[#737478] leading-relaxed">
                Cluster disparate phishing domains, smishing waves, and rogue Android APK loaders into unified threat campaigns with attributed actor tracking.
              </p>
            </div>

            <div className="pt-2 space-y-2 text-xs text-[#111312] font-semibold">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                <span>Shared infrastructure & IP clustering</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#2F7C5B] shrink-0" />
                <span>Targeted region & victim impact estimation</span>
              </div>
            </div>
          </Card>

        </div>
      </section>

      {/* SECTION C: HOW IT WORKS (5-STEP WORKFLOW) */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold text-[#434346] uppercase tracking-wider bg-[#EFEFEA] px-3 py-1 rounded-full border border-[#DCDAD4]">
            End-to-End Orchestration
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#111312] tracking-tight">
            How BrandShield Protects You
          </h2>
          <p className="text-xs sm:text-sm text-[#434346] leading-relaxed">
            From cryptographic ownership verification to autonomous takedowns in minutes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[
            { step: '01', title: 'Verify Your Brand', desc: 'Publish DNS TXT record to prove domain authority.', icon: Fingerprint },
            { step: '02', title: 'Discover Candidates', desc: 'AI crawler monitors 40,000+ domain changes / hr.', icon: Search },
            { step: '03', title: 'Analyze AI Evidence', desc: 'Perceptual hash + NLP urgency scoring engine.', icon: Cpu },
            { step: '04', title: 'Investigate Threats', desc: 'Cluster related IoCs and campaign syndicates.', icon: Layers },
            { step: '05', title: 'Monitor & Takedown', desc: 'Dispatched directly to registrar abuse desks.', icon: Send },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.step} className="p-6 rounded-2xl bg-white border border-[#E2E1DC] shadow-sm space-y-3 relative group hover:-translate-y-1 transition-all">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xl font-extrabold text-[#111312]">{item.step}</span>
                  <div className="p-2 rounded-xl bg-[#111312] text-[#FBF5A5]">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <h4 className="text-sm font-bold text-[#111312]">{item.title}</h4>
                <p className="text-xs text-[#737478] leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>



      {/* SECTION E: EXPLAINABLE AI ARCHITECTURE */}
      <section id="explainable-ai" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold text-[#434346] uppercase tracking-wider bg-[#EFEFEA] px-3 py-1 rounded-full border border-[#DCDAD4]">
            Transparent Decision Logic
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#111312] tracking-tight">
            Explainable AI Risk Scoring
          </h2>
          <p className="text-xs sm:text-sm text-[#434346] leading-relaxed">
            Every risk score is backed by inspectable telemetry, verifiable evidence hashes, and human oversight.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          {[
            { title: '1. Ingestion Feeds', desc: 'DNS transparency logs, WHOIS registrations, and verified customer reports.', badge: 'Telemetry Layer' },
            { title: '2. Perceptual Matching', desc: 'Computer vision compares SVG strokes, layout similarity, and brand color tokens.', badge: 'Visual AI' },
            { title: '3. Behavioral Scoring', desc: 'NLP detects credential traps, fake urgency keywords, and external C2 sinks.', badge: 'RiskGuard Model' },
            { title: '4. Human Verification', desc: 'SOC analysts confirm abuse before dispatching legal takedown packages.', badge: 'Human in the Loop' },
          ].map((step) => (
            <div key={step.title} className="p-6 rounded-2xl bg-white border border-[#E2E1DC] shadow-sm space-y-3 relative group">
              <span className="text-[10px] font-bold text-[#111312] uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#FBF5A5] border border-[#FBF5A5] inline-block">
                {step.badge}
              </span>
              <h4 className="text-sm font-extrabold text-[#111312] mt-2">{step.title}</h4>
              <p className="text-xs text-[#737478] leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION F: SEPARATE USER PATHWAYS */}
      <section id="portals" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold text-[#434346] uppercase tracking-wider bg-[#EFEFEA] px-3 py-1 rounded-full border border-[#DCDAD4]">
            Dual-Portal Architecture
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#111312] tracking-tight">
            Choose Your Experience
          </h2>
          <p className="text-xs sm:text-sm text-[#434346] leading-relaxed">
            Tailored workspaces designed specifically for enterprise security teams and vigilant consumers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          
          {/* Card 1: For Brand Owners (Solid Near-Black Card) */}
          <div className="p-8 sm:p-10 rounded-3xl bg-[#111312] text-white border border-[#2B2D2C] shadow-2xl flex flex-col justify-between group">
            <div className="space-y-4">
              <div className="w-13 h-13 rounded-2xl bg-[#FBF5A5] text-[#111312] flex items-center justify-center group-hover:scale-105 transition-transform shadow-sm">
                <Building2 className="w-6 h-6" />
              </div>

              <div>
                <span className="text-[10px] font-bold text-[#FBF5A5] uppercase tracking-wider">For Organizations</span>
                <h3 className="text-2xl font-extrabold text-white mt-0.5">Brand Owner Portal</h3>
                <p className="text-xs text-[#9A9B9C] mt-2 leading-relaxed">
                  Monitor authenticated domains, review AI risk evidence, automate abuse takedowns, and respond to customer trust reviews.
                </p>
              </div>

              <div className="space-y-2 pt-2 text-xs text-[#D6D6D8] font-medium">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#FBF5A5] shrink-0" />
                  <span>Sub-minute domain typosquatting alerts</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#FBF5A5] shrink-0" />
                  <span>Automated registrar takedown desk</span>
                </div>
              </div>
            </div>

            <div className="pt-8 mt-6 border-t border-[#262827] flex items-center gap-3">
              <button
                onClick={() => handleSelectRoleAndNavigate('brand_owner', '/brand-owner/overview')}
                className="flex-1 py-3 px-4 rounded-xl bg-[#FBF5A5] hover:bg-[#F6EF8A] text-[#111312] text-xs font-bold shadow-sm flex items-center justify-center gap-2 group-hover:gap-3 transition-all"
              >
                <span>Enter Brand Portal</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => handleSelectRoleAndNavigate('brand_owner', '/auth/brand-register')}
                className="py-3 px-4 rounded-xl bg-[#1C1E1D] hover:bg-[#252726] text-white text-xs font-semibold border border-[#2D2F2E] transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>

          {/* Card 2: For Customers (Solid Editorial White Card) */}
          <div className="p-8 sm:p-10 rounded-3xl bg-white border border-[#D5D4CE] shadow-sm flex flex-col justify-between group">
            <div className="space-y-4">
              <div className="w-13 h-13 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center group-hover:scale-105 transition-transform shadow-sm">
                <User className="w-6 h-6" />
              </div>

              <div>
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider">For Consumers</span>
                <h3 className="text-2xl font-extrabold text-[#111312] mt-0.5">Customer Portal</h3>
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

            <div className="pt-8 mt-6 border-t border-[#EAE9E4] flex items-center gap-3">
              <button
                onClick={() => handleSelectRoleAndNavigate('customer', '/customer')}
                className="flex-1 py-3 px-4 rounded-xl bg-[#111312] hover:bg-[#232524] text-[#FBF5A5] text-xs font-bold flex items-center justify-center gap-2 group-hover:gap-3 transition-all"
              >
                <span>Enter Customer Portal</span>
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
      </section>



      {/* SECTION H: PREMIUM NEAR-BLACK FOOTER */}
      <footer className="bg-[#111312] text-white border-t border-[#2B2D2C] py-12 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#FBF5A5] flex items-center justify-center text-[#111312]">
                <Shield className="w-4 h-4 fill-[#111312]" />
              </div>
              <span className="font-extrabold text-sm text-white tracking-tight">BrandShield AI</span>
            </div>
            <p className="text-xs text-[#9A9B9C] leading-relaxed">
              Next-generation digital risk protection and impersonation defense built with editorial precision.
            </p>
          </div>

          <div>
            <h5 className="text-xs font-bold text-[#FBF5A5] uppercase tracking-wider mb-3">Enterprise Solutions</h5>
            <ul className="space-y-2 text-xs text-[#9A9B9C]">
              <li><Link to="/brand-owner/overview" className="hover:text-[#FBF5A5] transition-colors">Brand Owner Dashboard</Link></li>
              <li><Link to="/brand-owner/brand-profile" className="hover:text-[#FBF5A5] transition-colors">DNS Domain Verification</Link></li>
              <li><Link to="/brand-owner/threat-overview" className="hover:text-[#FBF5A5] transition-colors">Automated Takedown API</Link></li>
              <li><Link to="/brand-owner/reports" className="hover:text-[#FBF5A5] transition-colors">Executive Risk Reporting</Link></li>
            </ul>
          </div>

          <div>
            <h5 className="text-xs font-bold text-[#FBF5A5] uppercase tracking-wider mb-3">Consumer Safety</h5>
            <ul className="space-y-2 text-xs text-[#9A9B9C]">
              <li><Link to="/customer/brands" className="hover:text-[#FBF5A5] transition-colors">Verified Brands Directory</Link></li>
              <li><Link to="/customer/report" className="hover:text-[#FBF5A5] transition-colors">Report Phishing Site</Link></li>
              <li><Link to="/customer/my-reports" className="hover:text-[#FBF5A5] transition-colors">My Reports Tracker</Link></li>
              <li><Link to="/customer/reviews" className="hover:text-[#FBF5A5] transition-colors">Community Reviews</Link></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h5 className="text-xs font-bold text-[#FBF5A5] uppercase tracking-wider">Demo Environment</h5>
            <div className="p-3.5 rounded-xl bg-[#1C1E1D] border border-[#2D2F2E] text-xs text-[#9A9B9C]">
              <p className="text-[11px] leading-snug">
                So-cio hackathon demo environment. Displayed metrics, IOCs, and alerts use realistic synthetic test datasets.
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto pt-8 mt-8 border-t border-[#262827] flex flex-col sm:flex-row items-center justify-between text-xs text-[#737478] gap-3">
          <div>&copy; 2026 So-cio &bull; ByteXL Hackathon Edition &bull; Editorial Design System</div>
          <div className="flex items-center gap-4">
            <span className="hover:text-[#FBF5A5] transition-colors cursor-pointer">Security Standards</span>
            <span>&bull;</span>
            <span className="hover:text-[#FBF5A5] transition-colors cursor-pointer">Privacy Guarantee</span>
            <span>&bull;</span>
            <span className="hover:text-[#FBF5A5] transition-colors cursor-pointer">Responsible Disclosure</span>
          </div>
        </div>
      </footer>
      </motion.div>

    </div>
  );
};
