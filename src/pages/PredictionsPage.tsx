import React from 'react';
import { BrainCircuit, Target, Zap, AlertTriangle, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils/cn';

const PREDICTIONS = [
  { symbol: 'RELIANCE', name: 'Reliance Ind.', probability: 78, direction: 'UP', volatility: 'LOW', expectedReturn: '+2.4%', timeframe: '5 Days' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', probability: 65, direction: 'UP', volatility: 'MODERATE', expectedReturn: '+1.2%', timeframe: '5 Days' },
  { symbol: 'INFY', name: 'Infosys', probability: 82, direction: 'DOWN', volatility: 'HIGH', expectedReturn: '-3.1%', timeframe: '5 Days' },
  { symbol: 'TCS', name: 'Tata Consultancy', probability: 54, direction: 'NEUTRAL', volatility: 'LOW', expectedReturn: '+0.2%', timeframe: '5 Days' },
  { symbol: 'ZOMATO', name: 'Zomato Ltd', probability: 88, direction: 'UP', volatility: 'HIGH', expectedReturn: '+5.5%', timeframe: '5 Days' },
  { symbol: 'ITC', name: 'ITC Ltd', probability: 60, direction: 'NEUTRAL', volatility: 'LOW', expectedReturn: '-0.1%', timeframe: '5 Days' },
];

export const PredictionsPage: React.FC = () => {
  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">AI Market Predictions</h1>
          <p className="text-slate-400">XGBoost directional forecasts powered by point-in-time technicals.</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <BrainCircuit className="w-4 h-4" />
          MODEL: XGB-DIR-V1.2
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="p-5 rounded-2xl bg-[#0a0a0a] border border-slate-800/50 flex flex-col justify-center">
          <div className="text-sm text-slate-400 mb-1">Model Accuracy (30D)</div>
          <div className="text-2xl font-bold text-white">68.4%</div>
        </div>
        <div className="p-5 rounded-2xl bg-[#0a0a0a] border border-slate-800/50 flex flex-col justify-center">
          <div className="text-sm text-slate-400 mb-1">High Confidence Signals</div>
          <div className="text-2xl font-bold text-emerald-400">14 Active</div>
        </div>
        <div className="p-5 rounded-2xl bg-[#0a0a0a] border border-slate-800/50 flex flex-col justify-center">
          <div className="text-sm text-slate-400 mb-1">Next Retraining In</div>
          <div className="text-2xl font-bold text-white">04:22:10</div>
        </div>
      </div>

      <div className="bg-[#0a0a0a] border border-slate-800/50 rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-slate-800/50 flex items-center gap-2">
          <Target className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-bold text-white">5-Day Directional Forecasts</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/50 text-xs uppercase tracking-wider text-slate-500 bg-white/[0.02]">
                <th className="p-4 font-medium">Asset</th>
                <th className="p-4 font-medium">Direction</th>
                <th className="p-4 font-medium">Probability</th>
                <th className="p-4 font-medium">Exp Return</th>
                <th className="p-4 font-medium">Volatility</th>
                <th className="p-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {PREDICTIONS.map((pred, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                  <td className="p-4">
                    <div className="font-bold text-white">{pred.symbol}</div>
                    <div className="text-xs text-slate-400">{pred.name}</div>
                  </td>
                  <td className="p-4">
                    <div className={cn(
                      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold",
                      pred.direction === 'UP' ? "bg-emerald-500/10 text-emerald-400" :
                      pred.direction === 'DOWN' ? "bg-rose-500/10 text-rose-400" :
                      "bg-slate-500/10 text-slate-400"
                    )}>
                      {pred.direction === 'UP' && <TrendingUp className="w-3 h-3" />}
                      {pred.direction === 'DOWN' && <TrendingDown className="w-3 h-3" />}
                      {pred.direction === 'NEUTRAL' && <Zap className="w-3 h-3" />}
                      {pred.direction}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={cn(
                            "h-full rounded-full",
                            pred.probability > 75 ? "bg-emerald-500" : pred.probability > 60 ? "bg-blue-500" : "bg-slate-500"
                          )}
                          style={{ width: `${pred.probability}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-white">{pred.probability}%</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "text-sm font-bold",
                      pred.expectedReturn.startsWith('+') ? "text-emerald-400" : 
                      pred.expectedReturn.startsWith('-') ? "text-rose-400" : "text-slate-400"
                    )}>
                      {pred.expectedReturn}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-xs font-medium text-slate-400 uppercase tracking-wider bg-slate-800/50 px-2 py-1 rounded">
                      {pred.volatility}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <button className="text-slate-400 hover:text-white p-2 transition-colors">
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
