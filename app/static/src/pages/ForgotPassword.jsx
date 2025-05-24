// ForgotPassword.jsx - app/static/src/pages/ForgotPassword.jsx
import React, { useState } from 'react';
import { Link, router } from '@inertiajs/react';
import { Mail, ArrowLeft, Heart, AlertCircle, CheckCircle } from 'lucide-react';

export default function ForgotPassword() {
    const [formData, setFormData] = useState({
        email: ''
    });
    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) return;
        
        setIsLoading(true);
        
        try {
            // Using Inertia.js to submit form
            router.post('/forgot-password', formData, {
                onSuccess: () => {
                    setIsSubmitted(true);
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

    if (isSubmitted) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-cyan-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
                <div className="max-w-md w-full space-y-8">
                    {/* Header */}
                    <div className="text-center">
                        <div className="flex justify-center items-center mb-6">
                            <div className="bg-green-500 p-3 rounded-full">
                                <CheckCircle className="w-8 h-8 text-white" />
                            </div>
                        </div>
                        <h2 className="text-3xl font-bold text-gray-900">Check your email</h2>
                        <p className="mt-2 text-sm text-gray-600">
                            We've sent password reset instructions to <strong>{formData.email}</strong>
                        </p>
                    </div>

                    {/* Success Card */}
                    <div className="bg-white rounded-xl shadow-lg p-8">
                        <div className="text-center space-y-4">
                            <div className="bg-green-50 p-4 rounded-lg">
                                <p className="text-sm text-green-800">
                                    If an account with that email exists, you'll receive an email with instructions 
                                    to reset your password within the next few minutes.
                                </p>
                            </div>
                            
                            <div className="text-sm text-gray-600">
                                <p>Didn't receive the email? Check your spam folder or</p>
                                <button 
                                    onClick={() => setIsSubmitted(false)}
                                    className="text-teal-600 hover:text-teal-500 font-medium"
                                >
                                    try again
                                </button>
                            </div>
                        </div>
                        
                        <div className="mt-6">
                            <Link 
                                href="/login"
                                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-colors"
                            >
                                Back to Sign In
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-cyan-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                {/* Header */}
                <div className="text-center">
                    <div className="flex justify-center items-center mb-6">
                        <div className="bg-teal-500 p-3 rounded-full">
                            <Heart className="w-8 h-8 text-white" />
                        </div>
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900">Forgot your password?</h2>
                    <p className="mt-2 text-sm text-gray-600">
                        No worries! Enter your email and we'll send you reset instructions.
                    </p>
                </div>

                {/* Forgot Password Form */}
                <div className="bg-white rounded-xl shadow-lg p-8">
                    {errors.general && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-500" />
                            <span className="text-sm text-red-700">{errors.general}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
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
                                    placeholder="Enter your email address"
                                />
                            </div>
                            {errors.email && (
                                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
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
                                    Sending instructions...
                                </div>
                            ) : (
                                'Send Reset Instructions'
                            )}
                        </button>
                    </form>

                    {/* Back to Login */}
                    <div className="mt-6 text-center">
                        <Link 
                            href="/login/" 
                            className="inline-flex items-center text-sm text-teal-600 hover:text-teal-500 font-medium"
                        >
                            <ArrowLeft className="w-4 h-4 mr-1" />
                            Back to Sign In
                        </Link>
                    </div>
                </div>

                {/* Additional Help */}
                <div className="text-center">
                    <p className="text-xs text-gray-500">
                        Need more help?{' '}
                        <Link href="/contact" className="text-teal-600 hover:text-teal-500">
                            Contact our support team
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}