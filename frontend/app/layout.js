import './globals.css';
import { ThemeProvider } from 'next-themes';
import { AISettingsProvider } from '@/hooks/use-ai-settings';
import { SITE_METADATA } from '@/lib/profile-data';

export const metadata = {
  title: SITE_METADATA.site.title,
  description: SITE_METADATA.site.description,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col" suppressHydrationWarning>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem={true}>
          <AISettingsProvider>
            {children}
          </AISettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

