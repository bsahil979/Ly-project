import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User as UserIcon,
  Sparkles,
  Info,
  Loader2,
  Zap,
  Globe,
  Brain,
  TrendingUp
} from 'lucide-react';
import { PortfolioService } from '../services/api';

const ChatAdvisor = ({ tickers = [] }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    
    // Initialize chat on first message
    if (!chatStarted) {
      setChatStarted(true);
    }
    
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      // Simulate AI 'Thinking' and fetch real context if tickers exist
      let aiResponse = "";
      
      if (tickers.length > 0) {
        // Try to get actual portfolio advice to power the chat
        try {
          const analysis = await PortfolioService.getAnalysis(tickers);
          const advice = analysis.decision_options?.recommendation || "Based on my quantitative analysis, your portfolio is currently stable. However, watch for volatility in the tech sector.";
          aiResponse = advice;
        } catch (err) {
          aiResponse = "I'm having trouble reaching my analytics engine right now, but looking at your watchlist, you have a diversified set of assets. How can I help you analyze a specific one?";
        }
      } else {
        aiResponse = "You haven't added any tickers to your portfolio yet! Add some assets in the Watchlist section so I can provide personalized financial advice.";
      }

      // Add slight delay for realism
      setTimeout(() => {
        setMessages(prev => [...prev, { role: 'assistant', text: aiResponse }]);
        setLoading(false);
      }, 800);

    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: "I'm sorry, I encountered an error processing your request." }]);
      setLoading(false);
    }
  };

  // Hero landing screen (before any messages)
  if (!chatStarted) {
    return (
      <div className="w-full min-h-[calc(100vh-200px)] bg-gradient-to-b from-[#0a0b10] via-[#0e1017] to-[#11131a] relative overflow-hidden">
        {/* Animated background gradient */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl animate-blob" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-blob animation-delay-2000" />
        </div>

        {/* Main content */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[calc(100vh-200px)]">
          
          {/* AI Powered Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600/10 border border-indigo-600/30 rounded-full mb-8 animate-in fade-in duration-500">
            <Zap className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-semibold text-indigo-300">AI-Powered</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-5xl md:text-6xl font-black text-center mb-6 leading-tight animate-in fade-in slide-in-from-bottom-4 duration-700">
            Enhance your <span className="text-indigo-400">market analysis</span> with AI
          </h1>

          {/* Subheading */}
          <p className="text-center text-gray-400 text-lg max-w-2xl mb-12 leading-relaxed animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            Get deep research from <span className="text-white font-semibold">AI agents</span> across <span className="text-white font-semibold">30+ global stock markets</span>, crypto, forex, and ETFs — delivered in <span className="text-white font-semibold">13 native languages</span>. Powered by real-time data.
          </p>

          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-12 w-full max-w-3xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-emerald-400 text-sm font-bold mb-1">
                <Globe className="w-4 h-4" />
                Live market data
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-emerald-400 text-sm font-bold mb-1">
                <Brain className="w-4 h-4" />
                8 AI research agents
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-emerald-400 text-sm font-bold mb-1">
                <TrendingUp className="w-4 h-4" />
                30+ exchanges
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-emerald-400 text-sm font-bold mb-1">
                <MessageSquare className="w-4 h-4" />
                13 languages
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-emerald-400 text-sm font-bold mb-1">
                <Zap className="w-4 h-4" />
                24/7 monitoring
              </div>
            </div>
          </div>

          {/* Chat Input Section */}
          <form onSubmit={handleSendMessage} className="w-full max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl blur opacity-0 group-hover:opacity-30 transition-all duration-500" />
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything..." 
                className="relative w-full bg-[#161720] border border-gray-800 rounded-2xl py-5 pl-6 pr-16 text-base focus:outline-none focus:ring-2 focus:ring-indigo-600/50 focus:border-transparent transition-all shadow-xl text-white placeholder-gray-500"
              />
              <button 
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg flex items-center gap-2 transition-all shadow-lg active:scale-95 disabled:opacity-50 font-semibold text-sm"
                disabled={loading || !input.trim()}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Ask AI
              </button>
            </div>
          </form>

          {/* Suggestion Pills */}
          <div className="flex flex-wrap gap-3 mt-8 justify-center max-w-2xl">
            <button onClick={() => setInput("Analyze my portfolio risk")} className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white bg-gray-800/30 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg transition-all">Analyze Risk</button>
            <button onClick={() => setInput("Give me a price forecast for my assets")} className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white bg-gray-800/30 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg transition-all">Get Forecast</button>
            <button onClick={() => setInput("What is the current market sentiment?")} className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white bg-gray-800/30 hover:bg-gray-800/60 border border-gray-700/50 rounded-lg transition-all">Sentiment</button>
          </div>
        </div>
      </div>
    );
  }

  // Chat interface (after first message)
  return (
    <div className="w-full h-[calc(100vh-200px)] flex flex-col bg-[#11131a]/80 backdrop-blur-3xl border border-gray-800/50 rounded-[2.5rem] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-500">
      
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
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth custom-scrollbar"
      >
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
        {loading && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-lg animate-pulse">
              <Bot className="w-6 h-6" />
            </div>
            <div className="bg-gray-800/50 p-5 rounded-2xl flex items-center gap-3">
              <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />
              <span className="text-xs text-gray-400 font-medium italic">Analyzing markets...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSendMessage} className="p-6 bg-[#0a0b10]/50 border-t border-gray-800/50">
        <div className="relative group">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your portfolio or the market..." 
            className="w-full bg-[#161720] border border-gray-800/80 rounded-2xl py-5 pl-7 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600/40 focus:border-indigo-600/50 transition-all shadow-inner text-white"
          />
          <button 
            type="submit"
            className="absolute right-3 top-1/2 -translate-y-1/2 w-11 h-11 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl flex items-center justify-center transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
            disabled={loading || !input.trim()}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="flex gap-4 mt-4">
          <button type="button" onClick={() => setInput("Analyze my portfolio risk")} className="text-[10px] uppercase tracking-wider font-bold text-gray-500 hover:text-indigo-400 transition-colors">Analyze Risk</button>
          <button type="button" onClick={() => setInput("Give me a price forecast for my assets")} className="text-[10px] uppercase tracking-wider font-bold text-gray-500 hover:text-indigo-400 transition-colors">Get Forecast</button>
          <button type="button" onClick={() => setInput("What is the current market sentiment?")} className="text-[10px] uppercase tracking-wider font-bold text-gray-500 hover:text-indigo-400 transition-colors">Sentiment Report</button>
        </div>
      </form>
    </div>
  );
};

export default ChatAdvisor;
