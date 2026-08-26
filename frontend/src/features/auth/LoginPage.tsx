import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { error: toastError, success: toastSuccess } = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toastError('Validation Error', 'Please enter email and password.');
      return;
    }

    setIsLoading(true);
    try {
      await login({ email, password });
      toastSuccess('Welcome Back!', 'Successfully authenticated.');
      navigate('/app/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      toastError('Authentication Failed', err.message || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Sign in to your CRM workspace</h2>
        <p className="text-xs text-slate-500 mt-1">Enter your organization email and password</p>
      </div>

      <Input
        label="Email Address"
        type="email"
        placeholder="name@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <Input
        label="Password"
        type="password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
        Sign In
      </Button>

      <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
        <span>Don't have an organization workspace yet? </span>
        <Link to="/register" className="font-semibold text-teal-700 hover:underline">
          Register Organization
        </Link>
      </div>
    </form>
  );
};
