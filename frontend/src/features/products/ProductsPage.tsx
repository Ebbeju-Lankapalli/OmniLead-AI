import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';
import { productsApi } from '@/api/products';
import { ProductResponse, ProductCreateRequest } from '@/types/api';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';

export const ProductsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductResponse | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [price, setPrice] = useState('0');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');

  const { data: products = [], isLoading, refetch } = useQuery({
    queryKey: ['products', searchTerm],
    queryFn: () => (searchTerm ? productsApi.search(searchTerm) : productsApi.list()),
  });

  const openAdd = () => {
    setEditingProduct(null);
    setName('');
    setSku('');
    setPrice('0');
    setCategory('');
    setDescription('');
    setShowAddModal(true);
  };

  const openEdit = (p: ProductResponse) => {
    setEditingProduct(p);
    setName(p.name);
    setSku(p.code || '');
    setPrice(String(p.price ?? 0));
    setCategory(p.category || '');
    setDescription(p.description || '');
    setShowAddModal(true);
  };

  // Save Mutation
  const saveMutation = useMutation({
    mutationFn: () => {
      const payload: ProductCreateRequest = {
        name: name.trim(),
        code: sku.trim() || null,
        price: price.trim() === '' ? null : Number(price),
        category: category.trim() || null,
        description: description.trim() || null,
      };
      return editingProduct
        ? productsApi.update(editingProduct.id, payload)
        : productsApi.create(payload);
    },
    onSuccess: () => {
      success(editingProduct ? 'Product Updated' : 'Product Created', 'Product catalog updated.');
      setShowAddModal(false);
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => {
      error('Save Failed', err.message || 'Could not save product.');
    },
  });

  // Activate / Deactivate
  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? productsApi.deactivate(id) : productsApi.activate(id),
    onSuccess: () => {
      success('Status Changed', 'Product active status updated.');
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Product Catalog Management</h2>
          <p className="text-xs text-slate-500 mt-1">
            Products, services, pricing tiers, and SKUs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={openAdd}>
            <Plus className="w-4 h-4 mr-1.5" /> Add Product
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card className="p-4 bg-white">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search products by name, SKU, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600"
          />
        </div>
      </Card>

      {/* Table */}
      <Card className="overflow-hidden bg-white">
        {isLoading ? (
          <LoadingSpinner message="Loading catalog..." />
        ) : products.length === 0 ? (
          <EmptyState title="No products found" description="No products match your search criteria." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">SKU</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Price</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs sm:text-sm text-slate-700">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">{p.name}</td>
                    <td className="py-3.5 px-4 text-slate-600 font-mono text-xs">{p.code || '—'}</td>
                    <td className="py-3.5 px-4 text-slate-600">{p.category || '—'}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">${(p.price ?? 0).toFixed(2)}</td>
                    <td className="py-3.5 px-4">
                      {p.is_active ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-400 text-xs">
                          <XCircle className="w-3.5 h-3.5" /> Inactive
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(p)}>
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleStatusMutation.mutate({ id: p.id, active: p.is_active })}
                      >
                        {p.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal */}
      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title={editingProduct ? 'Edit Product' : 'Add New Product'}>
        <div className="space-y-4">
          <Input label="Product Name *" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="SKU" value={sku} onChange={(e) => setSku(e.target.value)} placeholder="SKU-1001" />
          <Input label="Price ($) *" type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} required />
          <Input label="Category" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Software / Hardware" />
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-900"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" disabled={!name.trim() || price.trim() === '' || Number.isNaN(Number(price)) || Number(price) < 0} onClick={() => saveMutation.mutate()} isLoading={saveMutation.isPending}>
              Save Product
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
