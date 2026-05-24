'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  name: string;
  url: string;
  icon: LucideIcon;
}

interface FloatingNavProps {
  items: NavItem[];
  logo?: React.ReactNode;
  cta?: React.ReactNode;
  className?: string;
}

export function FloatingNav({ items, logo, cta, className }: FloatingNavProps) {
  const [isMobile, setIsMobile] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  const isActive = (item: NavItem) => pathname === item.url;

  return (
    <div className={cn('fixed top-0 inset-x-0 z-50 pt-4 flex justify-center', className)}>
      <div className="flex items-center gap-1 border border-gray-200/60 bg-white/70 backdrop-blur-xl backdrop-saturate-150 py-1 px-1.5 rounded-full shadow-[0_2px_20px_-2px_rgba(0,0,0,0.06)]">
        {logo && <div className="flex items-center pl-2.5 pr-1">{logo}</div>}

        <div className="hidden md:flex items-center gap-0.5">
          {items.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);
            return (
              <Link
                key={item.name}
                href={item.url}
                className={cn(
                  'relative cursor-pointer text-sm px-4 py-1.5 rounded-full transition-colors',
                  'text-gray-500 hover:text-gray-900',
                  active && 'text-gray-900'
                )}
              >
                <span className="hidden md:inline">{item.name}</span>
                {active && (
                  <motion.div
                    layoutId="tubelight"
                    className="absolute inset-0 w-full bg-gray-100 rounded-full -z-10"
                    initial={false}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  >
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-1 bg-gray-900 rounded-t-full">
                      <div className="absolute w-12 h-6 bg-gray-900/10 rounded-full blur-md -top-2 -left-2" />
                      <div className="absolute w-8 h-6 bg-gray-900/10 rounded-full blur-md -top-1" />
                      <div className="absolute w-4 h-4 bg-gray-900/10 rounded-full blur-sm top-0 left-2" />
                    </div>
                  </motion.div>
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex md:hidden items-center gap-0.5">
          {items.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);
            return (
              <Link
                key={item.name}
                href={item.url}
                className={cn(
                  'relative cursor-pointer p-2 rounded-full transition-colors',
                  'text-gray-500 hover:text-gray-900',
                  active && 'text-gray-900'
                )}
              >
                <Icon size={18} strokeWidth={2.5} />
                {active && (
                  <motion.div
                    layoutId="tubelight-mobile"
                    className="absolute inset-0 w-full bg-gray-100 rounded-full -z-10"
                    initial={false}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  >
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-gray-900 rounded-t-full">
                      <div className="absolute w-8 h-4 bg-gray-900/10 rounded-full blur-md -top-1 -left-1" />
                    </div>
                  </motion.div>
                )}
              </Link>
            );
          })}
        </div>

        {cta && <div className="flex items-center gap-1.5 pl-1 shrink-0">{cta}</div>}
      </div>
    </div>
  );
}
