import React from 'react';
import { Link } from 'react-router-dom';
import {
  MessageSquare,
  Sparkles,
  Target,
  Clock,
  BarChart3,
  PhoneCall,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              O
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">OmniLead AI</span>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 lg:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5 text-teal-600" />
          <span>Enterprise Omnichannel Lead Intelligence Platform</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 max-w-4xl mx-auto leading-tight">
          Turn every customer enquiry into an{' '}
          <span className="text-teal-600 underline decoration-teal-300 decoration-wavy underline-offset-4">
            actionable sales opportunity
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto font-normal leading-relaxed">
          Unify leads from Instagram, WhatsApp, Meta campaigns, phone calls, and manual entries. Automated AI scoring, purchase-intent detection, and explainable priority queues empower your sales team.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link to="/register">
            <Button size="lg" className="w-full sm:w-auto px-8 gap-2 shadow-md">
              <span>Start Managing Leads</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="outline" size="lg" className="w-full sm:w-auto px-8">
              Explore Demo Workspace
            </Button>
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
          <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm flex items-start gap-3">
            <MessageSquare className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Unified Inbox</h4>
              <p className="text-[11px] text-slate-500 mt-0.5">WhatsApp, IG & Meta Ads</p>
            </div>
          </div>
          <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm flex items-start gap-3">
            <Target className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Intent Scoring</h4>
              <p className="text-[11px] text-slate-500 mt-0.5">0-100 Purchase Intent</p>
            </div>
          </div>
          <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm flex items-start gap-3">
            <Clock className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Follow-Up Risk</h4>
              <p className="text-[11px] text-slate-500 mt-0.5">Prevent Lead Stagnation</p>
            </div>
          </div>
          <div className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-slate-900">Human Review</h4>
              <p className="text-[11px] text-slate-500 mt-0.5">Human-in-the-Loop Audit</p>
            </div>
          </div>
        </div>
      </section>

      {/* Product Capabilities Section */}
      <section className="py-16 bg-white border-t border-b border-slate-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Built for Modern High-Velocity Sales Teams
            </h2>
            <p className="text-sm text-slate-600 mt-2">
              OmniLead AI combines automatic channel ingestion, explainable AI scoring, and structured sales workflows in a classic modern CRM interface.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Explainable AI Scoring</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                No black-box predictions. Every lead receives transparent scores for Lead Quality, Purchase Intent, and Follow-Up Risk with full factor breakdowns.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                <PhoneCall className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Call Intelligence</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Upload sales call audio to automatically extract transcripts, sentiment, objections, commitments, and recommended next best actions.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Natural-Language Search</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Query leads naturally e.g. "Show high intent leads assigned to John with overdue follow-ups". The system parses structured filters instantly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 bg-slate-900 text-slate-400 text-xs border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white">OmniLead AI</span>
            <span>© 2026 Production Lead Intelligence System</span>
          </div>
          <div className="flex gap-6 text-slate-400">
            <Link to="/login" className="hover:text-white">Sign In</Link>
            <Link to="/register" className="hover:text-white">Create Account</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
