import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Music Video Generator',
  description: 'AI music video generator — personal build',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
