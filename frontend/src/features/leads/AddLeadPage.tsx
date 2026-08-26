import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowLeft, User, Package } from 'lucide-react';
import { leadsApi } from '@/api/leads';
import { customersApi } from '@/api/customers';
import { productsApi } from '@/api/products';
import { LeadSource, LeadCreateRequest } from '@/types/api';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';

export const AddLeadPage: React.FC = () => {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [customerMode, setCustomerMode] = useState<'new' | 'existing'>('new');
  const [selectedCustomerId, setSelectedCustomerId] = useState('');

  // New Customer Fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [companyName, setCompanyName] = useState('');

  // Lead Details
  const [source, setSource] = useState<LeadSource>(LeadSource.MANUAL);
  const [statusId, setStatusId] = useState('');
  const [productId, setProductId] = useState('');
  const [notes, setNotes] = useState('');

  // Queries
  const {
    data: statuses = [],
    isLoading: areStatusesLoading,
    error: statusesError,
  } = useQuery({
    queryKey: ['lead-statuses'],
    queryFn: () => leadsApi.listStatuses(),
  });

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.list(),
  });

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.list(),
  });

  // Set default initial status to NEW (or first status if NEW isn't found) once statuses load
  useEffect(() => {
    if (statuses.length > 0 && !statusId) {
      const defaultStatus = statuses.find((st) => st.key === 'NEW') || statuses[0];
      if (defaultStatus) {
        setStatusId(defaultStatus.id);
      }
    }
  }, [statuses, statusId]);

  useEffect(() => {
    if (statusesError) {
      error(
        'Status Loading Failed',
        statusesError instanceof Error
          ? statusesError.message
          : 'Could not load lead statuses.'
      );
    }
  }, [error, statusesError]);

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: async () => {
      const defaultStatusId = statuses.find((st) => st.key === 'NEW')?.id || statuses[0]?.id;
      const finalStatusId = statusId || defaultStatusId;

      if (!finalStatusId) {
        throw new Error('No lead status is available. Please reload the page and try again.');
      }

      let finalCustomerId = selectedCustomerId;

      if (customerMode === 'new') {
        const newCustomer = await customersApi.create({
          full_name: fullName,
          primary_email: email.trim() || undefined,
          primary_phone: phone.trim() || undefined,
          company_name: companyName || undefined,
        });
        finalCustomerId = newCustomer.id;
      }

      const payload: LeadCreateRequest = {
        customer_id: finalCustomerId,
        status_id: finalStatusId,
        source,
        product_id: productId || undefined,
        requirement: notes || undefined,
      };

      return leadsApi.create(payload);
    },
    onSuccess: (lead) => {
      success('Lead Created', 'New sales lead added to the pipeline.');
      navigate(`/app/leads/${lead.id}`);
    },
    onError: (err: unknown) => {
      error(
        'Creation Failed',
        err instanceof Error ? err.message : 'Could not create lead.'
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customerMode === 'new' && !fullName) {
      error('Validation Error', 'Customer Full Name is required.');
      return;
    }
    if (customerMode === 'existing' && !selectedCustomerId) {
      error('Validation Error', 'Please select an existing customer.');
      return;
    }
    createMutation.mutate();
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button
        onClick={() => navigate('/app/leads')}
        className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Leads Directory
      </button>

      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Create New Sales Lead</h2>
        <p className="text-xs text-slate-500 mt-1">
          Add customer details, acquisition channel, and initial interest context.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Customer Information Card */}
        <Card className="p-6 bg-white space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <User className="w-4 h-4 text-teal-600" /> Customer Information
            </h3>
            <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-md">
              <button
                type="button"
                onClick={() => setCustomerMode('new')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  customerMode === 'new' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
                }`}
              >
                New Customer
              </button>
              <button
                type="button"
                onClick={() => setCustomerMode('existing')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                  customerMode === 'existing' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
                }`}
              >
                Existing Customer
              </button>
            </div>
          </div>

          {customerMode === 'existing' ? (
            <Select
              label="Select Customer"
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              options={customers.map((c) => ({
                label: `${c.full_name} ${c.company_name ? `(${c.company_name})` : ''}`,
                value: c.id,
              }))}
              required
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Full Name *"
                placeholder="e.g. Michael Scott"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
              <Input
                label="Company Name"
                placeholder="e.g. Dunder Mifflin"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
              <Input
                label="Email Address"
                type="email"
                placeholder="michael@dundermifflin.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Input
                label="Phone Number"
                type="tel"
                placeholder="+1 555 019 2831"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          )}
        </Card>

        {/* Lead Context Card */}
        <Card className="p-6 bg-white space-y-4">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center gap-2">
            <Package className="w-4 h-4 text-teal-600" /> Lead Pipeline Context
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Lead Source / Channel"
              value={source}
              onChange={(e) => setSource(e.target.value as LeadSource)}
              options={Object.values(LeadSource).map((src) => ({
                label: src,
                value: src,
              }))}
            />

            <Select
              label="Initial Status"
              value={statusId}
              onChange={(e) => setStatusId(e.target.value)}
              placeholder={areStatusesLoading ? 'Loading statuses...' : 'Select a status'}
              disabled={areStatusesLoading || statuses.length === 0}
              required
              options={statuses.map((st) => ({
                label: st.name,
                value: st.id,
              }))}
            />

            <div className="sm:col-span-2">
              <Select
                label="Product Interest (Optional)"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                options={products.map((p) => ({
                  label: p.price != null ? `${p.name} ($${p.price})` : p.name,
                  value: p.id,
                }))}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Notes / Requirements</label>
            <textarea
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record any specific customer requests, budget details, or background context..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/app/leads')}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={createMutation.isPending}
            disabled={areStatusesLoading || statuses.length === 0}
          >
            Create Lead
          </Button>
        </div>
      </form>
    </div>
  );
};
