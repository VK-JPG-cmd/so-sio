import React, { useState, useEffect } from 'react';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { SecurityAlert, ThreatSeverity } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { 
  Bell, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ArrowRight, 
  ShieldAlert, 
  ExternalLink,
  Filter,
  Check
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const AlertsPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<SecurityAlert[]>([]);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [filterRead, setFilterRead] = useState<string>('all');

  useEffect(() => {
    const load = async () => {
      if (currentBrand) {
        const data = await threatService.getAlerts(currentBrand.id);
        setAlerts(data);
        setFilteredAlerts(data);
      }
    };
    load();
  }, [currentBrand]);

  useEffect(() => {
    let result = [...alerts];
    if (selectedSeverity !== 'all') {
      result = result.filter(a => a.severity === selectedSeverity);
    }
    if (filterRead === 'unread') {
      result = result.filter(a => !a.isRead);
    } else if (filterRead === 'read') {
      result = result.filter(a => a.isRead);
    }
    setFilteredAlerts(result);
  }, [selectedSeverity, filterRead, alerts]);

  const handleMarkAsRead = async (alertId: string) => {
    await threatService.markAlertRead(alertId);
    setAlerts(alerts.map(a => a.id === alertId ? { ...a, isRead: true } : a));
    showToast({ type: 'info', title: 'Alert Marked Read', message: 'Notification dismissed.' });
  };

  const handleMarkAllRead = async () => {
    for (const a of alerts) {
      if (!a.isRead) await threatService.markAlertRead(a.id);
    }
    setAlerts(alerts.map(a => ({ ...a, isRead: true })));
    showToast({ type: 'success', title: 'All Alerts Read', message: 'All pending notifications marked as reviewed.' });
  };

  const unreadCount = alerts.filter(a => !a.isRead).length;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Security Alerts</h1>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full bg-rose-500 text-white text-xs font-bold animate-pulse">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <p className="text-xs text-brand-muted mt-1">
            Real-time critical, high, medium, and low-priority alerts with direct navigation to threats and campaigns.
          </p>
        </div>

        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={handleMarkAllRead} leftIcon={<Check className="w-4 h-4" />}>
            Mark All as Reviewed
          </Button>
        )}
      </div>

      {/* Priority Filters */}
      <Card padding="sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-bold text-brand-muted uppercase text-[10px]">Filter Priority:</span>
            {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-colors ${
                  selectedSeverity === sev
                    ? 'bg-[#111312] text-[#FBF5A5] border border-[#111312]'
                    : 'text-brand-muted hover:bg-brand-surface-light border border-transparent'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <select
              value={filterRead}
              onChange={(e) => setFilterRead(e.target.value)}
              className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-brand-surface-light border border-brand-border text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="all">All Alerts</option>
              <option value="unread">Unread Only</option>
              <option value="read">Reviewed Only</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Alerts Feed */}
      <div className="space-y-3">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map((alert) => (
            <Card 
              key={alert.id} 
              padding="sm" 
              className={`transition-all ${
                alert.isRead 
                  ? 'opacity-75 bg-white/70' 
                  : alert.severity === 'critical'
                    ? 'bg-white border-l-4 border-l-rose-500 shadow-soft'
                    : 'bg-white border-l-4 border-l-orange-500 shadow-soft'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className={`p-2.5 rounded-2xl shrink-0 mt-0.5 ${
                    alert.severity === 'critical' ? 'bg-rose-50 text-rose-700' :
                    alert.severity === 'high' ? 'bg-orange-50 text-orange-700' :
                    alert.severity === 'medium' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'
                  }`}>
                    <Bell className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-xs font-bold text-brand-dark">{alert.title}</h4>
                      <Badge severity={alert.severity} size="sm" />
                      {!alert.isRead && (
                        <span className="w-2 h-2 rounded-full bg-rose-500 shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-brand-muted mt-0.5 leading-relaxed">{alert.message}</p>
                    <span className="text-[10px] text-brand-muted/70">{alert.timestamp}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {!alert.isRead && (
                    <Button variant="ghost" size="sm" onClick={() => handleMarkAsRead(alert.id)}>
                      Mark Read
                    </Button>
                  )}
                  {alert.actionUrl && (
                    <Link to={alert.actionUrl}>
                      <Button variant="secondary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                        Investigate
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            </Card>
          ))
        ) : (
          <div className="p-12 text-center text-xs text-brand-muted bg-white rounded-3xl border border-brand-border">
            No alerts found matching your selected filter.
          </div>
        )}
      </div>

    </div>
  );
};
