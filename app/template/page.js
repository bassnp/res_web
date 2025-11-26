'use client';

import { Home, Settings, ArrowLeft } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

// ============================================
// DYNAMIC PAGE TEMPLATE
// ============================================
// This template provides a reusable structure for creating new pages.
// Simply copy this file to a new folder under /app and customize.
// Example: /app/projects/[slug]/page.js for dynamic project pages

// Reusable Header Component
const PageHeader = ({ title }) => {
  const [settingsOpen, setSettingsOpen] = useState(false);

  const navItems = [
    { name: 'About', href: '/#about' },
    { name: 'Projects', href: '/#projects' },
    { name: 'Experience', href: '/#experience' },
    { name: 'Contact', href: '/#contact' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-eggshell/80 backdrop-blur-md border-b border-twilight/10">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <a href="/" className="p-2 rounded-lg hover:bg-twilight/10 transition-colors">
            <Home className="w-6 h-6 text-twilight" />
          </a>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className="px-4 py-2 text-sm font-medium text-twilight hover:text-burnt-peach transition-colors rounded-lg hover:bg-twilight/5"
              >
                {item.name}
              </a>
            ))}
          </nav>

          <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
            <DialogTrigger asChild>
              <button className="p-2 rounded-lg hover:bg-twilight/10 transition-colors">
                <Settings className="w-6 h-6 text-twilight" />
              </button>
            </DialogTrigger>
            <DialogContent className="bg-eggshell border-twilight/20">
              <DialogHeader>
                <DialogTitle className="text-twilight">Settings</DialogTitle>
              </DialogHeader>
              <div className="py-6 text-center text-twilight/60">
                <p>Settings panel - Coming soon</p>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </header>
  );
};

// Page Content Component
const PageContent = () => {
  return (
    <section className="min-h-screen pt-24 pb-16">
      <div className="container mx-auto px-6">
        {/* Back navigation */}
        <a 
          href="/"
          className="inline-flex items-center gap-2 text-twilight/60 hover:text-burnt-peach transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </a>

        {/* Page Title */}
        <h1 className="text-4xl md:text-5xl font-bold text-twilight mb-6">
          <span className="text-burnt-peach">Template</span> Page
        </h1>

        {/* Content Section */}
        <div className="prose prose-lg max-w-none">
          <p className="text-twilight/70 text-lg leading-relaxed mb-8">
            This is a dynamic page template designed for easy customization. 
            Use this structure to create new pages for projects, blog posts, 
            or any other content.
          </p>

          {/* Example Content Card */}
          <div className="bg-white rounded-2xl p-8 shadow-lg mb-8">
            <h2 className="text-2xl font-semibold text-twilight mb-4">
              How to Use This Template
            </h2>
            <ol className="list-decimal list-inside space-y-3 text-twilight/70">
              <li>Copy this file to a new folder under <code className="bg-twilight/5 px-2 py-1 rounded">/app</code></li>
              <li>Rename the folder to match your desired URL path</li>
              <li>Customize the content, title, and sections as needed</li>
              <li>For dynamic routes, use <code className="bg-twilight/5 px-2 py-1 rounded">[slug]</code> folder naming</li>
            </ol>
          </div>

          {/* Example Section */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-burnt-peach/10 to-apricot/10 rounded-xl p-6">
              <h3 className="text-xl font-semibold text-twilight mb-3">Features</h3>
              <ul className="space-y-2 text-twilight/70">
                <li>Responsive design</li>
                <li>Consistent styling</li>
                <li>Reusable components</li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-muted-teal/10 to-twilight/10 rounded-xl p-6">
              <h3 className="text-xl font-semibold text-twilight mb-3">Benefits</h3>
              <ul className="space-y-2 text-twilight/70">
                <li>Maintainable codebase</li>
                <li>Fast development</li>
                <li>Consistent UX</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// Footer Component
const PageFooter = () => {
  return (
    <footer className="bg-twilight text-eggshell py-8">
      <div className="container mx-auto px-6 text-center">
        <p className="text-eggshell/70">
          &copy; {new Date().getFullYear()} Portfolio. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

// Main Export
export default function TemplatePage() {
  return (
    <>
      <PageHeader />
      <main>
        <PageContent />
      </main>
      <PageFooter />
    </>
  );
}
