'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Minus, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

const COLOR_SCHEMES = [
  { bg: 'bg-gray-900', text: 'text-white', answer: 'bg-gray-200 text-gray-900' },
  { bg: 'bg-gray-800', text: 'text-white', answer: 'bg-gray-300 text-gray-900' },
  { bg: 'bg-gray-700', text: 'text-white', answer: 'bg-gray-200 text-gray-800' },
  { bg: 'bg-gray-600', text: 'text-white', answer: 'bg-gray-300 text-gray-800' },
  { bg: 'bg-gray-500', text: 'text-white', answer: 'bg-gray-200 text-gray-700' },
  { bg: 'bg-gray-400', text: 'text-white', answer: 'bg-gray-300 text-gray-700' },
] as const;

interface FAQItem {
  id: number;
  question: string;
  answer: string;
}

interface FaqAccordionProps {
  data: FAQItem[];
  className?: string;
}

export function FaqAccordion({ data, className }: FaqAccordionProps) {
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <div className={cn('p-4', className)}>
      {data.map((item, i) => {
        const isOpen = openId === item.id;
        const colors = COLOR_SCHEMES[i % COLOR_SCHEMES.length];
        return (
          <div key={item.id} className="mb-3">
            <button onClick={() => setOpenId(isOpen ? null : item.id)} className="flex w-full items-center justify-start gap-x-4">
              <div className={cn('relative flex items-center space-x-2 rounded-2xl p-3.5 px-5 transition-all duration-300 text-base', isOpen ? `${colors.bg} ${colors.text}` : 'bg-gray-100 text-gray-700 hover:bg-gray-200')}>
                <span className="font-medium">{item.question}</span>
              </div>
              <span className={cn('text-gray-400 transition-colors duration-300', isOpen && 'text-gray-900')}>
                {isOpen ? <Minus className="h-5 w-5" /> : <Plus className="h-5 w-5" />}
              </span>
            </button>
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.4 }} className="overflow-hidden">
                  <div className="ml-8 mt-2 md:ml-16">
                    <div className={cn('relative max-w-lg rounded-2xl px-5 py-3.5 text-base leading-relaxed', colors.answer)}>
                      {item.answer}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
