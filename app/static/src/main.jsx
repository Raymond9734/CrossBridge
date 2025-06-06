import "vite/modulepreload-polyfill";
import { createRoot } from "react-dom/client";
import { createInertiaApp, router } from "@inertiajs/react";
import { InertiaProgress } from '@inertiajs/progress';
import axios from 'axios';
import React from 'react';
import getCookie from "./utils/cookieUtils";

// Import TailwindCSS styles
import './styles/main.css';



document.addEventListener('DOMContentLoaded', () => {
    // Get CSRF token from meta tag first, then fallback to cookie
    const pages = import.meta.glob('./pages/**/*.jsx');
    const csrfMeta = document.querySelector('meta[name=csrf-token]');
    const csrfFromMeta = csrfMeta?.textContent || csrfMeta?.getAttribute('content') || '';
    const csrfFromCookie = getCookie('csrftoken');
    const csrfToken = csrfFromMeta || csrfFromCookie;
    
    
    // Set CSRF token for axios
    if (csrfToken) {
        axios.defaults.headers.common['X-CSRF-Token'] = csrfToken;
        axios.defaults.headers.common['X-CSRFToken'] = csrfToken;
    }
    
    // Configure Inertia to use the CSRF token for all requests
    router.on('before', (event) => {
        if (['post', 'put', 'patch', 'delete'].includes(event.detail.visit.method.toLowerCase())) {
            const currentToken = csrfFromMeta || getCookie('csrftoken');
            if (currentToken) {
                event.detail.visit.headers = {
                    ...event.detail.visit.headers,
                    'X-CSRFToken': currentToken,
                    'X-CSRF-Token': currentToken,
                };
            }
        }
    });

    InertiaProgress.init({
        // Customize the progress bar to match healthcare theme
        color: '#14b8a6', // teal-500
        showSpinner: true,
    });

    createInertiaApp({
        resolve: (name) => {
            const page = pages[`./pages/${name}.jsx`];
            if (!page) {
                throw new Error(`Page ${name} not found`);
            }
            return page();
        },
        setup({ el, App, props }) {
            const root = createRoot(el);
            root.render(<App {...props} />);
        },
    });
});