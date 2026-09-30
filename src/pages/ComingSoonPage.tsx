import React from 'react';
import { Construction } from 'lucide-react';
import { useLocation } from 'react-router-dom';

export const ComingSoonPage: React.FC = () => {
  const location = useLocation();
  const pathName = location.pathname.split('/').pop()?.replace('-', ' ') || 'Page';
  
  return (
    <div className="h-full flex flex-col items-center justify-center p-8 text-center animate-fadeIn">
      <div className="w-16 h-16 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-6 border border-emerald-500/20">
        <Construction className="w-8 h-8 text-emerald-400" />
      </div>
      <h1 className="text-3xl font-bold text-white mb-4 capitalize">
        {pathName}
      </h1>
      <p className="text-slate-400 max-w-md">
        We are currently engineering this module for the FinPulse AI Platform. Check back soon for updates!
      </p>
    </div>
  );
};
