import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { 
  UserCheck, 
  Phone, 
  Mail, 
  ShieldCheck, 
  CheckCircle2, 
  LogOut, 
  ExternalLink,
  Award,
  Sparkles
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export const CustomerProfilePage: React.FC = () => {
  const { user, signOut, switchRole } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Customer Profile & Security Status</h1>
        <p className="text-xs text-brand-muted mt-1">
          Manage your verified contact credentials, security badges, and report history.
        </p>
      </div>

      {/* User Info Card */}
      <Card className="bg-white border-[#E2E1DC]">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <img
              src={user?.avatarUrl || 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80'}
              alt={user?.name}
              className="w-16 h-16 rounded-3xl object-cover border border-brand-border shadow-sm"
            />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-brand-dark">{user?.name || 'David Chen'}</h2>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Phone OTP Verified
                </span>
              </div>
              <p className="text-xs text-brand-muted flex items-center gap-1">
                <Mail className="w-3.5 h-3.5" /> {user?.email || 'david.chen@gmail.com'}
              </p>
              <p className="text-xs text-brand-muted flex items-center gap-1">
                <Phone className="w-3.5 h-3.5" /> {user?.phone || '+1 (555) 902-1144'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                signOut();
                navigate('/auth');
              }}
              leftIcon={<LogOut className="w-4 h-4" />}
            >
              Sign Out
            </Button>
          </div>
        </div>
      </Card>

      {/* Community Protection Badges */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-brand-dark">Community Cyber Guardian Badges</h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-white border border-brand-border shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#F4F3EF] text-[#111312] border border-[#E2E1DC] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-brand-dark">Verified Reporter</h4>
              <p className="text-[10px] text-brand-muted">Phone authenticated submission tier</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-brand-border shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-brand-dark">Fraud Buster Level 2</h4>
              <p className="text-[10px] text-brand-muted">3 phishing kits neutralized</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-brand-border shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-brand-dark">Community Advocate</h4>
              <p className="text-[10px] text-brand-muted">Helpful reviews acknowledged by brands</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Switch Persona Card */}
      <Card className="bg-white border-[#E2E1DC] shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-xs font-bold text-brand-dark">Enterprise Brand Security Representative?</h4>
            <p className="text-xs text-brand-muted mt-0.5">Switch to Brand Owner Intelligence Dashboard to manage brand assets and automated takedowns.</p>
          </div>

          <button
            onClick={() => {
              switchRole('brand_owner');
              navigate('/brand-owner/overview');
            }}
            className="px-4 py-2 rounded-2xl bg-gradient-btn hover:bg-gradient-btn-hover text-white text-xs font-bold shadow-soft shrink-0"
          >
            Switch to Brand Portal
          </button>
        </div>
      </Card>

    </div>
  );
};
