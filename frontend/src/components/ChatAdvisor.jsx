import React from 'react';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User as UserIcon,
  Sparkles,
  Info
} from 'lucide-react';

const ChatAdvisor = () => {
  const [messages, setMessages] = React.useState([
    { role: 'assistant', text: "Hello! I'm your Smart Financial Advisor. I've analyzed your portfolio and the current market regime. How can I help you today?" },
    { role: 'user', text: "What's the outlook for NVDA based on current sentiment?" },
    { role: 'assistant', text: "NVDA is showing strong positive sentiment (0.82) across news headlines. Social signals have also spiked following the latest earnings preview. My LSTM model suggests a 12% upside potential over the next 14 days, though volatility remains high." },
  ]);

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-200px)] flex flex-col bg-[#11131a]/80 backdrop-blur-3xl border border-gray-800/50 rounded-[2.5rem] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-500">
      
      {/* Chat Header */}
      <div className="p-6 border-b border-gray-800/50 flex items-center justify-between bg-gradient-to-r from-transparent via-indigo-600/5 to-transparent">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-600/20 ring-4 ring-indigo-600/10">
            <Bot className="w-7 h-7 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-gray-100 flex items-center gap-2">
              AI Wealth Advisor 
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            </h3>
            <p className="text-xs text-indigo-400 font-bold uppercase tracking-widest">Powered by Gemini & FinBERT</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="p-2.5 rounded-xl hover:bg-gray-800/50 text-gray-500 transition-all"><Info className="w-5 h-5" /></button>
          <button className="p-2.5 rounded-xl hover:bg-gray-800/50 text-gray-500 transition-all"><Sparkles className="w-5 h-5 text-yellow-500" /></button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-4 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${
              m.role === 'assistant' 
                ? 'bg-indigo-600 text-white' 
                : 'bg-gray-800 text-gray-400'
            }`}>
              {m.role === 'assistant' ? <Bot className="w-6 h-6" /> : <UserIcon className="w-6 h-6" />}
            </div>
            
            <div className={`max-w-[75%] p-5 rounded-2xl text-sm leading-relaxed shadow-sm ${
              m.role === 'assistant' 
                ? 'bg-gray-800/50 text-gray-200 border-l-4 border-indigo-600' 
                : 'bg-indigo-600 text-white font-medium ml-12 rounded-tr-none'
            }`}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-6 bg-[#0a0b10]/50 border-t border-gray-800/50">
        <div className="relative group">
          <input 
            type="text" 
            placeholder="Ask anything about your portfolio or the market..." 
            className="w-full bg-[#161720] border border-gray-800/80 rounded-2xl py-5 pl-7 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600/40 focus:border-indigo-600/50 transition-all shadow-inner"
          />
          <button className="absolute right-3 top-1/2 -translate-y-1/2 w-11 h-11 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl flex items-center justify-center transition-all shadow-lg shadow-indigo-600/20 active:scale-95">
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="flex gap-4 mt-4">
          <button className="text-[10px] uppercase tracking-wider font-bold text-gray-500 hover:text-indigo-400 transition-colors">Analyze Risk</button>
          <button className="text-[10px] uppercase tracking-wider font-bold text-gray-500 hover:text-indigo-400 transition-colors">Get Forecast</button>
          <button className="text-[10px] uppercase tracking-wider font-bold text-gray-500 hover:text-indigo-400 transition-colors">Sentiment Report</button>
        </div>
      </div>
    </div>
  );
};

export default ChatAdvisor;
