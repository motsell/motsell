import type { Metadata } from 'next';
import './styles.css';

export const metadata: Metadata = { title: 'Fixture notes', description: 'Local synthetic Next app' };

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><header><span>Fixture notes</span></header><main>{children}</main></body></html>;
}
