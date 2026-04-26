import type { Metadata } from 'next';
import { DM_Mono, Bebas_Neue } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const dmMono = DM_Mono({
  weight: ['300', '400', '500'],
  subsets: ['latin'],
  variable: '--font-dm-mono',
});

const bebasNeue = Bebas_Neue({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-bebas-neue',
});

export const metadata: Metadata = {
  title: 'Roomy Dashboard',
  description: 'Smart home inventory management',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${dmMono.variable} ${bebasNeue.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
