import './globals.css';
import { ThemeProvider } from 'next-themes';
import { AISettingsProvider } from '@/hooks/use-ai-settings';

export const metadata = {
  title: 'Portfolio | Software Engineer',
  description: 'Personal resume and portfolio showcasing projects and work experience',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem={true}>
          <AISettingsProvider>
            {children}
          </AISettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

