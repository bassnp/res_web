import './globals.css';
import { ThemeProvider } from 'next-themes';

export const metadata = {
  title: 'Portfolio | Software Engineer',
  description: 'Personal resume and portfolio showcasing projects and work experience',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem={true}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
