import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const { error: toastError, success: toastSuccess } = useToast();

  const [fullName, setFullName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [organizationSlug, setOrganizationSlug] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleOrgNameChange = (val: string) => {
    setOrganizationName(val);
    if (!organizationSlug) {
      setOrganizationSlug(val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !organizationName || !organizationSlug || !email || !password) {
      toastError('Validation Error', 'All fields are required.');
      return;
    }

    if (password.length < 8) {
      toastError('Validation Error', 'Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        full_name: fullName,
        organization_name: organizationName,
        organization_slug: organizationSlug,
        email,
        password,
      });
      toastSuccess('Registration Successful!', 'Organization and administrator account created.');
      navigate('/app/dashboard');
    } catch (err: any) {
      console.error('Registration error:', err);
      toastError('Registration Failed', err.message || 'Unable to register organization.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Create Organization Workspace</h2>
        <p className="text-xs text-slate-500 mt-1">Set up your company and first administrator account</p>
      </div>

      <Input
        label="Your Full Name"
        type="text"
        placeholder="Jane Doe"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        required
      />

      <Input
        label="Organization Name"
        type="text"
        placeholder="Acme Sales Corp"
        value={organizationName}
        onChange={(e) => handleOrgNameChange(e.target.value)}
        required
      />

      <Input
        label="Organization URL Slug"
        type="text"
        placeholder="acme-sales"
        value={organizationSlug}
        onChange={(e) => setOrganizationSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]+/g, ''))}
        helperText="Used for internal domain scoping"
        required
      />

      <Input
        label="Administrator Email"
        type="email"
        placeholder="admin@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <Input
        label="Password (min 8 characters)"
        type="password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
        Create Organization
      </Button>

      <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
        <span>Already have an account? </span>
        <Link to="/login" className="font-semibold text-teal-700 hover:underline">
          Sign In
        </Link>
      </div>
    </form>
  );
};
