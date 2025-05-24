import "vite/modulepreload-polyfill";
import { createRoot } from "react-dom/client";
import { createInertiaApp } from "@inertiajs/react";
import { InertiaProgress } from '@inertiajs/progress';
import axios from 'axios';
import React from 'react';

// Import TailwindCSS styles
import './styles/main.css';

document.addEventListener('DOMContentLoaded', () => {
    const csrfMeta = document.querySelector('meta[name=csrf-token]');
    const csrfToken = csrfMeta?.textContent || '';
    axios.defaults.headers.common['X-CSRF-Token'] = csrfToken;
    const pages = import.meta.glob('./pages/**/*.jsx');

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