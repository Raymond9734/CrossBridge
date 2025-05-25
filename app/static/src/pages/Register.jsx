import React, { useState } from 'react';
import { Link, router } from '@inertiajs/react';
import { Eye, EyeOff, Mail, Lock, User, Phone, Heart, AlertCircle, CheckCircle } from 'lucide-react';

export default function Register() {
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: '',
        role: 'patient', // Default to patient
        terms: false
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.firstName.trim()) {
            newErrors.firstName = 'First name is required';
        }
        
        if (!formData.lastName.trim()) {
            newErrors.lastName = 'Last name is required';
        }
        
        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }
        
        if (!formData.phone) {
            newErrors.phone = 'Phone number is required';
        } else if (!/^\+?[\d\s\-\(\)]{10,}$/.test(formData.phone)) {
            newErrors.phone = 'Please enter a valid phone number';
        }
        
        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters';
        } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
            newErrors.password = 'Password must contain uppercase, lowercase, and number';
        }
        
        if (!formData.confirmPassword) {
            newErrors.confirmPassword = 'Please confirm your password';
        } else if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }
        
        if (!formData.terms) {
            newErrors.terms = 'You must accept the terms and conditions';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) return;
        
        setIsLoading(true);
        
        try {
            router.post('/register/', formData, {
                onSuccess: () => {
                    window.location.reload()
                },
                onError: (errors) => {
                    setErrors(errors);
                },
                onFinish: () => {
                    setIsLoading(false);
                }
            });
        } catch (error) {
            setIsLoading(false);
            setErrors({ general: 'An error occurred. Please try again.' });
        }
    };

    const getPasswordStrength = (password) => {
        if (password.length === 0) return { strength: 0, text: '', color: '' };
        if (password.length < 6) return { strength: 25, text: 'Weak', color: 'bg-red-500' };
        if (password.length < 8) return { strength: 50, text: 'Fair', color: 'bg-yellow-500' };
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) return { strength: 75, text: 'Good', color: 'bg-blue-500' };
        return { strength: 100, text: 'Strong', color: 'bg-green-500' };
    };

    const passwordStrength = getPasswordStrength(formData.password);

    return (
        <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-cyan-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl w-full space-y-8">
                {/* Header */}
                <div className="text-center">
                    <div className="flex justify-center items-center mb-6">
                        <div className="bg-teal-500 p-3 rounded-full">
                            <Heart className="w-8 h-8 text-white" />
                        </div>
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900">Join CareBridge</h2>
                    <p className="mt-2 text-sm text-gray-600">
                        Create your healthcare account to get started
                    </p>
                </div>

                {/* Registration Form */}
                <div className="bg-white rounded-xl shadow-lg p-8">
                    {errors.general && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-500" />
                            <span className="text-sm text-red-700">{errors.general}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Role Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-3">
                                I am registering as a:
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                                <label className={`relative flex items-center p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                                    formData.role === 'patient' 
                                        ? 'border-teal-500 bg-teal-50' 
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}>
                                    <input
                                        type="radio"
                                        name="role"
                                        value="patient"
                                        checked={formData.role === 'patient'}
                                        onChange={handleInputChange}
                                        className="sr-only"
                                    />
                                    <div className="flex-1">
                                        <div className="flex items-center">
                                            <User className="w-5 h-5 text-teal-600 mr-2" />
                                            <span className="font-medium text-gray-900">Patient</span>
                                        </div>
                                        <p className="text-sm text-gray-600 mt-1">Book appointments and manage health records</p>
                                    </div>
                                    {formData.role === 'patient' && (
                                        <CheckCircle className="w-5 h-5 text-teal-500" />
                                    )}
                                </label>

                                <label className={`relative flex items-center p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                                    formData.role === 'doctor' 
                                        ? 'border-teal-500 bg-teal-50' 
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}>
                                    <input
                                        type="radio"
                                        name="role"
                                        value="doctor"
                                        checked={formData.role === 'doctor'}
                                        onChange={handleInputChange}
                                        className="sr-only"
                                    />
                                    <div className="flex-1">
                                        <div className="flex items-center">
                                            <Heart className="w-5 h-5 text-teal-600 mr-2" />
                                            <span className="font-medium text-gray-900">Doctor</span>
                                        </div>
                                        <p className="text-sm text-gray-600 mt-1">Manage patients and appointments</p>
                                    </div>
                                    {formData.role === 'doctor' && (
                                        <CheckCircle className="w-5 h-5 text-teal-500" />
                                    )}
                                </label>
                            </div>
                        </div>

                        {/* Name Fields */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                                    First Name
                                </label>
                                <input
                                    id="firstName"
                                    name="firstName"
                                    type="text"
                                    value={formData.firstName}
                                    onChange={handleInputChange}
                                    className={`block w-full px-3 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none transition-colors ${
                                        errors.firstName 
                                            ? 'border-red-300 focus:border-red-500' 
                                            : 'border-gray-300 focus:border-teal-500'
                                    }`}
                                    placeholder="Enter your first name"
                                />
                                {errors.firstName && (
                                    <p className="mt-1 text-sm text-red-600">{errors.firstName}</p>
                                )}
                            </div>

                            <div>
                                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                                    Last Name
                                </label>
                                <input
                                    id="lastName"
                                    name="lastName"
                                    type="text"
                                    value={formData.lastName}
                                    onChange={handleInputChange}
                                    className={`block w-full px-3 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none transition-colors ${
                                        errors.lastName 
                                            ? 'border-red-300 focus:border-red-500' 
                                            : 'border-gray-300 focus:border-teal-500'
                                    }`}
                                    placeholder="Enter your last name"
                                />
                                {errors.lastName && (
                                    <p className="mt-1 text-sm text-red-600">{errors.lastName}</p>
                                )}
                            </div>
                        </div>

                        {/* Email Field */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                Email Address
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Mail className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none transition-colors ${
                                        errors.email 
                                            ? 'border-red-300 focus:border-red-500' 
                                            : 'border-gray-300 focus:border-teal-500'
                                    }`}
                                    placeholder="Enter your email"
                                />
                            </div>
                            {errors.email && (
                                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                            )}
                        </div>

                        {/* Phone Field */}
                        <div>
                            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                                Phone Number
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Phone className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    id="phone"
                                    name="phone"
                                    type="tel"
                                    value={formData.phone}
                                    onChange={handleInputChange}
                                    className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none transition-colors ${
                                        errors.phone 
                                            ? 'border-red-300 focus:border-red-500' 
                                            : 'border-gray-300 focus:border-teal-500'
                                    }`}
                                    placeholder="Enter your phone number"
                                />
                            </div>
                            {errors.phone && (
                                <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
                            )}
                        </div>

                        {/* Password Fields */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                    Password
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Lock className="h-5 w-5 text-gray-400" />
                                    </div>
                                    <input
                                        id="password"
                                        name="password"
                                        type={showPassword ? 'text' : 'password'}
                                        value={formData.password}
                                        onChange={handleInputChange}
                                        className={`block w-full pl-10 pr-10 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none transition-colors ${
                                            errors.password 
                                                ? 'border-red-300 focus:border-red-500' 
                                                : 'border-gray-300 focus:border-teal-500'
                                        }`}
                                        placeholder="Create password"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                                    >
                                        {showPassword ? (
                                            <EyeOff className="h-5 w-5 text-gray-400" />
                                        ) : (
                                            <Eye className="h-5 w-5 text-gray-400" />
                                        )}
                                    </button>
                                </div>
                                {formData.password && (
                                    <div className="mt-2">
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-gray-600">Password strength:</span>
                                            <span className={`font-medium ${
                                                passwordStrength.strength >= 75 ? 'text-green-600' : 
                                                passwordStrength.strength >= 50 ? 'text-yellow-600' : 'text-red-600'
                                            }`}>
                                                {passwordStrength.text}
                                            </span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                                            <div 
                                                className={`h-1.5 rounded-full transition-all ${passwordStrength.color}`}
                                                style={{ width: `${passwordStrength.strength}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                )}
                                {errors.password && (
                                    <p className="mt-1 text-sm text-red-600">{errors.password}</p>
                                )}
                            </div>

                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                    Confirm Password
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Lock className="h-5 w-5 text-gray-400" />
                                    </div>
                                    <input
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        type={showConfirmPassword ? 'text' : 'password'}
                                        value={formData.confirmPassword}
                                        onChange={handleInputChange}
                                        className={`block w-full pl-10 pr-10 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none transition-colors ${
                                            errors.confirmPassword 
                                                ? 'border-red-300 focus:border-red-500' 
                                                : 'border-gray-300 focus:border-teal-500'
                                        }`}
                                        placeholder="Confirm password"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                                    >
                                        {showConfirmPassword ? (
                                            <EyeOff className="h-5 w-5 text-gray-400" />
                                        ) : (
                                            <Eye className="h-5 w-5 text-gray-400" />
                                        )}
                                    </button>
                                </div>
                                {errors.confirmPassword && (
                                    <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
                                )}
                            </div>
                        </div>

                        {/* Terms Checkbox */}
                        <div>
                            <div className="flex items-start">
                                <div className="flex items-center h-5">
                                    <input
                                        id="terms"
                                        name="terms"
                                        type="checkbox"
                                        checked={formData.terms}
                                        onChange={handleInputChange}
                                        className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
                                    />
                                </div>
                                <div className="ml-3 text-sm">
                                    <label htmlFor="terms" className="text-gray-700">
                                        I agree to the{' '}
                                        <Link href="/terms" className="text-teal-600 hover:text-teal-500 font-medium">
                                            Terms of Service
                                        </Link>
                                        {' '}and{' '}
                                        <Link href="/privacy" className="text-teal-600 hover:text-teal-500 font-medium">
                                            Privacy Policy
                                        </Link>
                                    </label>
                                </div>
                            </div>
                            {errors.terms && (
                                <p className="mt-1 text-sm text-red-600">{errors.terms}</p>
                            )}
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? (
                                <div className="flex items-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                    Creating account...
                                </div>
                            ) : (
                                'Create Account'
                            )}
                        </button>
                    </form>

                    {/* Login Link */}
                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            Already have an account?{' '}
                            <Link 
                                href="/login/" 
                                className="font-medium text-teal-600 hover:text-teal-500"
                            >
                                Sign in here
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}