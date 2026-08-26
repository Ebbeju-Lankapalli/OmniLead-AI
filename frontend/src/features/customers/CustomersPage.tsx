import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, RefreshCw, Edit2, Archive } from 'lucide-react';
import { customersApi } from '@/api/customers';
import { CustomerResponse, CustomerCreateRequest } from '@/types/api';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { formatDate } from '@/lib/utils';

export const CustomersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<CustomerResponse | null>(null);

  // Customer Form State
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [location, setLocation] = useState('');
  const [customerType, setCustomerType] = useState('');
  const [notesSummary, setNotesSummary] = useState('');

  const { data: customers = [], isLoading, refetch } = useQuery({
    queryKey: ['customers', searchTerm],
    queryFn: () => (searchTerm ? customersApi.search(searchTerm) : customersApi.list()),
  });

  const openAdd = () => {
    setEditingCustomer(null);
    setFullName('');
    setEmail('');
    setPhone('');
    setCompanyName('');
    setLocation('');
    setCustomerType('');
    setNotesSummary('');
    setShowAddModal(true);
  };

  const openEdit = (c: CustomerResponse) => {
    setEditingCustomer(c);
    setFullName(c.full_name ?? '');
    setEmail(c.primary_email ?? '');
    setPhone(c.primary_phone ?? '');
    setCompanyName(c.company_name ?? '');
    setLocation(c.location ?? '');
    setCustomerType(c.customer_type ?? '');
    setNotesSummary(c.notes_summary ?? '');
    setShowAddModal(true);
  };

  // Create or Update Mutation
  const saveMutation = useMutation({
    mutationFn: () => {
      const payload: CustomerCreateRequest = {
        full_name: fullName.trim() || null,
        company_name: companyName.trim() || null,
        primary_email: email.trim() || null,
        primary_phone: phone.trim() || null,
        location: location.trim() || null,
        customer_type: customerType.trim() || null,
        notes_summary: notesSummary.trim() || null,
      };
      return editingCustomer
        ? customersApi.update(editingCustomer.id, payload)
        : customersApi.create(payload);
    },
    onSuccess: () => {
      success(editingCustomer ? 'Customer Updated' : 'Customer Created', 'Customer directory updated.');
      setShowAddModal(false);
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: (err: any) => {
      error('Save Failed', err.message || 'Could not save customer.');
    },
  });

  // Archive Mutation
  const archiveMutation = useMutation({
    mutationFn: (id: string) => customersApi.archive(id),
    onSuccess: () => {
      success('Archived', 'Customer archived.');
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Customer Directory</h2>
          <p className="text-xs text-slate-500 mt-1">
            Unified profile records across all channels and touchpoints.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={openAdd}>
            <Plus className="w-4 h-4 mr-1.5" /> Add Customer
          </Button>
        </div>
      </div>

      {/* Search Input */}
      <Card className="p-4 bg-white">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search customers by name, email, phone, company, or social handle..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600"
          />
        </div>
      </Card>

      {/* Directory Table */}
      <Card className="overflow-hidden bg-white">
        {isLoading ? (
          <LoadingSpinner message="Loading customer directory..." />
        ) : customers.length === 0 ? (
          <EmptyState title="No customers found" description="No customer records match your query." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Customer Name</th>
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4">Contact Info</th>
                  <th className="py-3 px-4">Location / Type</th>
                  <th className="py-3 px-4">Created</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs sm:text-sm text-slate-700">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">{c.full_name}</td>
                    <td className="py-3.5 px-4 text-slate-600">{c.company_name || '—'}</td>
                    <td className="py-3.5 px-4 text-xs">
                      <div>{c.primary_email || '—'}</div>
                      <div className="text-slate-400">{c.primary_phone || ''}</div>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">
                      <div>{c.location || '—'}</div>
                      {c.customer_type && (
                        <div className="text-slate-400">{c.customer_type}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-500">{formatDate(c.created_at)}</td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(c)}>
                        <Edit2 className="w-3.5 h-3.5 text-slate-500" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => archiveMutation.mutate(c.id)}>
                        <Archive className="w-3.5 h-3.5 text-rose-500" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title={editingCustomer ? 'Edit Customer Profile' : 'Add New Customer'}
      >
        <div className="space-y-4">
          <Input
            label="Full Name *"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Jane Doe"
            required
          />
          <Input
            label="Company Name"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Acme Inc"
          />
          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="jane@acme.com"
          />
          <Input
            label="Phone Number"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1 555 019 2831"
          />
          <Input
            label="Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Vijayawada"
          />
          <Input
            label="Customer Type"
            value={customerType}
            onChange={(e) => setCustomerType(e.target.value)}
            placeholder="Individual or Business"
          />
          <Input
            label="Notes"
            value={notesSummary}
            onChange={(e) => setNotesSummary(e.target.value)}
            placeholder="Important customer notes"
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!fullName.trim()}
              onClick={() => saveMutation.mutate()}
              isLoading={saveMutation.isPending}
            >
              Save Customer
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
