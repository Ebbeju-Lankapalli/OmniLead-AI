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

      {/* Navbar */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold text-base">
              O
            </div>
            <span className="text-lg font-bold tracking-tight">
              OmniLead AI
            </span>
          </Link>

          <div className="flex items-center gap-2">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>

            <Link to="/register">
              <Button size="sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Compact Hero */}
      <main className="flex-1">

        <section className="px-5 pt-14 pb-12">
          <div className="max-w-5xl mx-auto text-center">

            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-[11px] font-semibold mb-5">
              <Sparkles className="w-3 h-3 text-teal-600" />
              Enterprise Omnichannel Lead Intelligence
            </div>

            {/* Heading */}
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 max-w-4xl mx-auto leading-[1.08]">
              Turn every customer enquiry into an{' '}
              <span className="text-teal-600">
                actionable sales opportunity
              </span>
            </h1>

            {/* Description */}
            <p className="mt-4 text-sm sm:text-base text-slate-600 max-w-2xl mx-auto leading-relaxed">
              Unify leads from Instagram, WhatsApp, Meta campaigns, phone
              calls, and manual entries with AI-powered scoring, purchase
              intent detection, and intelligent follow-ups.
            </p>

            {/* CTA */}
            <div className="mt-7 flex flex-col sm:flex-row gap-3 justify-center items-center">
              <Link to="/register">
                <Button
                  size="lg"
                  className="w-full sm:w-auto px-6 gap-2"
                >
                  Start Managing Leads
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>

              <Link to="/login">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full sm:w-auto px-6"
                >
                  Explore Demo Workspace
                </Button>
              </Link>
            </div>

            {/* Feature Highlights */}
            <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-3 max-w-4xl mx-auto text-left">

              <div className="p-3 rounded-lg border border-slate-200 bg-white flex items-center gap-2.5">
                <MessageSquare className="w-4 h-4 text-teal-600 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold">Unified Inbox</h4>
                  <p className="text-[10px] text-slate-500">
                    WhatsApp, IG & Meta Ads
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white flex items-center gap-2.5">
                <Target className="w-4 h-4 text-teal-600 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold">Intent Scoring</h4>
                  <p className="text-[10px] text-slate-500">
                    0–100 Purchase Intent
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white flex items-center gap-2.5">
                <Clock className="w-4 h-4 text-teal-600 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold">Follow-Up Risk</h4>
                  <p className="text-[10px] text-slate-500">
                    Prevent Lead Stagnation
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-white flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold">Human Review</h4>
                  <p className="text-[10px] text-slate-500">
                    Human-in-the-Loop Audit
                  </p>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* Capabilities */}
        <section className="border-t border-slate-200 bg-white px-5 py-10">
          <div className="max-w-6xl mx-auto">

            <div className="text-center max-w-xl mx-auto mb-8">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight">
                Built for Modern Sales Teams
              </h2>

              <p className="text-xs sm:text-sm text-slate-600 mt-2 leading-relaxed">
                AI-powered lead intelligence combined with practical CRM
                workflows for high-velocity sales teams.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-4">

              {/* AI Scoring */}
              <div className="p-5 rounded-xl border border-slate-200 bg-slate-50">
                <div className="w-9 h-9 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center mb-3">
                  <Sparkles className="w-4 h-4" />
                </div>

                <h3 className="text-sm font-bold">
                  Explainable AI Scoring
                </h3>

                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  Transparent Lead Quality, Purchase Intent, and Follow-Up
                  Risk scores with clear factor breakdowns.
                </p>
              </div>

              {/* Call Intelligence */}
              <div className="p-5 rounded-xl border border-slate-200 bg-slate-50">
                <div className="w-9 h-9 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center mb-3">
                  <PhoneCall className="w-4 h-4" />
                </div>

                <h3 className="text-sm font-bold">
                  Call Intelligence
                </h3>

                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  Extract transcripts, sentiment, objections, commitments,
                  and recommended next actions from sales calls.
                </p>
              </div>

              {/* Natural Language */}
              <div className="p-5 rounded-xl border border-slate-200 bg-slate-50">
                <div className="w-9 h-9 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center mb-3">
                  <BarChart3 className="w-4 h-4" />
                </div>

                <h3 className="text-sm font-bold">
                  Natural-Language Search
                </h3>

                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  Search your leads naturally using queries such as
                  "high intent leads with overdue follow-ups."
                </p>
              </div>

            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="py-5 bg-slate-900 text-slate-400 text-[11px]">
        <div className="max-w-6xl mx-auto px-5 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white">
              OmniLead AI
            </span>
            <span>
              © 2026 Production Lead Intelligence System
            </span>
          </div>

          <div className="flex gap-5">
            <Link
              to="/login"
              className="hover:text-white"
            >
              Sign In
            </Link>

            <Link
              to="/register"
              className="hover:text-white"
            >
              Create Account
            </Link>
          </div>
        </div>
      </footer>

    </div>
  );
};
