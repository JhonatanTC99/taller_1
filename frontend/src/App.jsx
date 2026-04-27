import { useState, useEffect, useRef} from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, FileText, HelpCircle, Send, 
  Loader2, Database, Sparkles, ChevronRight, Zap, Clock 
} from 'lucide-react';
import dollarcityLogo from './assets/Logo.png';
import ReactMarkdown from 'react-markdown';

const App = () => {
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [question, setQuestion] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // ESTADOS AUTOMÁTICOS
  const [latency, setLatency] = useState(0);
  const [wordCount, setWordCount] = useState(0);
  
  // Iniciamos en null o vacío para que el sistema sepa que debe buscarlo
  const [aiModel, setAiModel] = useState('Sincronizando...'); 

  const API_URL = "http://localhost:8000/api";
    
  const [messages, setMessages] = useState([]);

  const messagesEndRef = useRef(null);

  // EFECTO DE SINCRONIZACIÓN INICIAL
  // Aquí es donde detectamos el modelo sin poner nombres manuales
  useEffect(() => {
    const syncEngine = async () => {
      try {
        const res = await fetch(`${API_URL}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: "identity_check" }) 
        });
        const data = await res.json();
        console.log("Respuesta del servidor al inicio:", data);
        if (data && data.model) {
          setAiModel(data.model);
        } else {
          setAiModel("Modelo Desconocido");
        }
    } catch (err) {
      console.error("Fallo de sincronización:", err);
      setAiModel("Servidor Offline");
      }
    };
    syncEngine();
  }, []);


  useEffect(() => {
    if (activeTab === 'chat') {
      const timeout = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);

      return () => clearTimeout(timeout);
    }
  }, [messages, activeTab]);

  // useEffect(() => {
  //   if (activeTab === 'summary' || activeTab === 'faq') {
  //     fetchData(activeTab);
  //   }
  // }, [activeTab]);

  const cleanAIResponse = (rawText) => {
    if (!rawText) return "";
    const xmlMatch = rawText.match(/<output>([\s\S]*?)<\/output>/i);
    if (xmlMatch && xmlMatch[1]) return xmlMatch[1].trim();
    
    let cleaned = rawText;
    const startMarkers = [/### ANÁLISIS INTERNO/i, /RESPUESTA_DEFINITIVA:/i, /Respuesta de la IA:/i];
    for (const marker of startMarkers) {
      const parts = cleaned.split(marker);
      if (parts.length > 1) { cleaned = parts.pop(); break; }
    }
    const final = cleaned.replace(/\(RAZONAMIENTO\)[\s\S]*?:/gi, '').trim();
    setWordCount(final.split(/\s+/).filter(w => w !== '').length); 
    return final;
  };

  const sendMessage = () => {
    if (!question.trim()) return;

    setMessages(prev => [
      ...prev,
      { role: 'user', content: question }
    ]);
    setIsTyping(true);

    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);

    if (!question.trim() || loading || isTyping) return;

    fetchData('chat', 'POST', { question });
  };

  const fetchData = async (endpoint, method = 'GET', body = null) => {
    const startTime = performance.now(); 
    setLoading(true);
    
    try {
      const config = { 
        method,
        headers: { 'Content-Type': 'application/json' },
        ...(body && { body: JSON.stringify({
            ...body,
            ...(aiModel && !aiModel.includes("Sincronizando") ? { model: aiModel } : {})
        })})
      };
      const res = await fetch(`${API_URL}/${endpoint}`, config);
      const data = await res.json();
      
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime)); 

      setAiModel(data?.model || "Modelo Desconocido");
      
      // Si el backend devuelve 'content', lo usamos; si es chat, suele ser 'content' también por tu _run_chain
      const cleaned = cleanAIResponse(data.content);
      if (endpoint === 'chat') {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: cleaned }
        ]);
        
        setIsTyping(false);
        setQuestion('');
      } else {
        setResult(cleaned);
      }

    } catch (err) {
      console.error("Error en la operación:", err);

      if (endpoint === 'chat') {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: 'Error: no se pudo conectar con el servidor.' }
        ]);
        setIsTyping(false);
      } else {
        setResult("Error: No se pudo conectar con el motor de IA.");
      }

      setAiModel("Error de Conexión");

    } finally {
      setLoading(false);
    }
  };
    const parseFAQ = (text) => {
      if (!text) return [];

      const cleanedText = text
        .replace(/\*\*/g, '')          // quita **
        .replace(/\n+/g, '\n')         // normaliza saltos de línea
        .trim();

      const blocks = cleanedText.split(/Pregunta:/).filter(Boolean);

      return blocks.map((block) => {
        const [questionPart, ...rest] = block.split('Respuesta:');
        
        return {
          question: questionPart?.trim(),
          answer: rest.join('Respuesta:')?.trim()
        };
      });
    };

  return (
    <div className="min-h-screen bg-[#FDFDFD] flex flex-col font-sans antialiased text-slate-900">
      
      {/* HEADER DINÁMICO */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b-4 border-[#00843D] p-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="relative">
              <img src={dollarcityLogo} alt="Logo" className="h-10 w-auto" />
              <motion.div 
                animate={{ scale: loading ? [1, 1.4, 1] : [1, 1.1, 1] }} 
                transition={{ repeat: Infinity, duration: loading ? 0.6 : 4 }}
                className={`absolute -top-1 -right-1 w-3 h-3 ${loading ? 'bg-amber-400' : 'bg-[#FFD200]'} rounded-full border-2 border-white shadow-sm`}
              />
            </div>
            <div>
              <h1 className="text-xl font-black text-gray-900 tracking-tight">Dollarcity <span className="text-[#00843D]">AI</span></h1>
              <div className="flex items-center gap-1">
                <Sparkles size={10} className="text-yellow-500 fill-yellow-500" />
                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Knowledge Assistant</p>
              </div>
            </div>
          </div>
          
          <div className="hidden md:flex gap-6 items-center">
            <div className="text-right border-r pr-6 border-gray-200">
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Módulo Académico</p>
              <p className="text-xs font-semibold text-gray-700 italic">TAAML - 2026</p>
            </div>

            {/* INDICADOR DE ESTADO REACTIVO AL LOADING */}
            <div className={`${loading ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'} px-4 py-1.5 rounded-full flex items-center gap-2 border transition-all duration-300`}>
              <div className={`w-2 h-2 ${loading ? 'bg-amber-500 animate-pulse' : 'bg-green-500 rounded-full animate-ping'}`} />
              <span className={`text-[10px] font-black ${loading ? 'text-amber-700' : 'text-green-700'} tracking-wider uppercase`}>
                {loading ? 'Procesando consulta...' : 'Sistema Listo'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4">
        
        {/* SIDEBAR CON WIDGET DE MOTOR */}
        <aside className="lg:col-span-3 space-y-6">
          <div className="bg-white p-3 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/40">
            <p className="text-[10px] font-black text-gray-400 px-4 py-3 uppercase tracking-widest">Funciones</p>
            <nav className="space-y-1">
              {['summary', 'faq', 'chat'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => { setActiveTab(tab); setResult(''); }}
                  className={`w-full flex items-center justify-between px-5 py-4 rounded-[1.8rem] font-bold transition-all ${
                    activeTab === tab 
                    ? 'bg-[#00843D] text-white shadow-lg shadow-green-200' 
                    : 'text-gray-500 hover:bg-slate-50 hover:text-[#00843D]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {tab === 'summary' ? <FileText size={18}/> : tab === 'faq' ? <HelpCircle size={18}/> : <MessageSquare size={18}/>}
                    <span className="text-sm capitalize">{tab}</span>
                  </div>
                  <ChevronRight size={14} className={activeTab === tab ? 'rotate-90' : 'opacity-20'} />
                </button>
              ))}
            </nav>
          </div>

          <div className="bg-white p-6 rounded-[2.5rem] shadow-xl shadow-slate-200/40 border border-slate-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                <Database size={20} />
              </div>
              <div>
                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-tighter">Motor Dollarcity</h4>
                <p className="text-xs font-bold text-gray-800">Sincronización Activa</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-gray-400 font-bold uppercase flex items-center gap-1"><Clock size={12}/> Latencia</span>
                <span className="text-gray-700 font-mono font-bold">{latency > 0 ? `${latency}ms` : '--'}</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-gray-400 font-bold uppercase flex items-center gap-1"><Zap size={12}/> Modelo</span>
                <span className="text-[#00843D] font-black italic">{aiModel}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* ÁREA DE CONTENIDO */}
        <section className="lg:col-span-9">
          <motion.div layout className ={`bg-white rounded-[3.5rem] shadow-2xl shadow-slate-300/20 border border-slate-100 p-10 min-h-[650px] flex flex-col relative justify-between"${
            activeTab === 'chat' && messages.length === 0
              ? 'min-h-[400px]'
              : 'min-h-[650px]'
          }`}
        >
            <div className="mb-10 flex justify-between items-start">
              
              <div>
                <h2 className="text-5xl font-black text-gray-900 tracking-tighter capitalize">
                  {activeTab}<span className="text-[#00843D]">.</span>
                </h2>
                <p className="text-gray-400 font-medium mt-3 text-lg">Operando sobre el motor {aiModel}</p>
              </div>
              {result && <div className="bg-slate-50 px-4 py-2 rounded-xl text-[10px] font-black text-slate-600 border border-slate-200">{wordCount} PALABRAS</div>}
            </div>

            {activeTab !== 'chat' && (
                <div className="mb-6 flex">
                    <button
                      onClick={() => fetchData(activeTab)}
                      disabled={loading}
                      className="bg-[#00843D] hover:bg-green-700 text-white px-8 py-4 rounded-2xl font-bold shadow-lg transition-all disabled:bg-slate-300"
                    >
                      {loading ? 'Procesando...' : `🗲  Generar ${activeTab}`}
                    </button>
                  </div>
                )}
          

            <div className="flex-1 bg-slate-100 rounded-[3rem] border border-dashed border-slate-200 p-2 overflow-hidden relative shadow-inner mb-6">
              <div className="h-full w-full overflow-y-auto p-6 custom-scrollbar text-slate-700">
                <AnimatePresence mode="wait">

                  {activeTab === 'chat' && messages.length === 0 && (
                    <div className="flex flex-col items-center py-5 opacity-40">
                      <p className="text-lg font-semibold text-gray-500">
                        Haz tu primera pregunta para iniciar la conversación con Dollie AI.
                      </p>
                    </div>
                  )}

                  {activeTab === 'chat' && messages.length > 0 ? (
                    <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                      {/* HISTORIAL */}
                      
                      {messages.map((msg, i) => (
                        <div key={i} className={msg.role === 'user' ? 'text-right' : 'text-left'}>
                          <div className={`inline-block px-4 py-3 rounded-2xl max-w-[70%] ${
                            msg.role === 'user' 
                              ? 'bg-[#00843D] text-white border-r-4 border-[#004d26] shadow-md'
                              : 'bg-white text-gray-800 border-l-4 border-[#00843D] shadow-sm'
                          }`}>
                            
                            {/* LABEL */}
                            <div className="text-xs mb-1 font-bold opacity-60">
                              {msg.role === 'user' ? 'Tú' : 'Dollie AI'}
                            </div>

                            {/* CONTENIDO */}
                            <ReactMarkdown>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        </div>
                      ))}
                      {activeTab === 'chat' && isTyping && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="text-left"
                      >
                        <div className="inline-block px-4 py-3 rounded-2xl bg-gray-100">
                          
                          <div className="flex items-center gap-2">
                            <span>Escribiendo</span>

                            {/* punticos animados */}
                            <div className="flex gap-1">
                              <motion.span
                                animate={{ opacity: [0.2, 1, 0.2] }}
                                transition={{ repeat: Infinity, duration: 1 }}
                              >.</motion.span>
                              <motion.span
                                animate={{ opacity: [0.2, 1, 0.2] }}
                                transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
                              >.</motion.span>
                              <motion.span
                                animate={{ opacity: [0.2, 1, 0.2] }}
                                transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
                              >.</motion.span>
                            </div>

                          </div>

                        </div>
                      </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>
                  ) : loading ? (
                    <div className="h-full flex flex-col items-center justify-center space-y-4">
                      <div className="w-16 h-16 border-4 border-slate-100 border-t-[#00843D] rounded-full animate-spin" />
                      <p className="text-[10px] font-black text-[#00843D] uppercase tracking-[0.4em] animate-pulse">Consultando Motor...</p>
                    </div>
                  ) : result ? (
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-slate-100 text-lg leading-relaxed">
                      
                      {activeTab === 'faq' ? (
                        <div className="space-y-8">
                          {parseFAQ(result).map((item, i) => (
                            <div key={i} className="mb-6">
                              
                              <p className="font-semibold text-slate-900 mb-2">
                              {item.question}
                              </p>

                              <p className="text-slate-700 leading-relaxed">
                                {item.answer}
                              </p>

                            </div>
                          ))}
                        </div>
                      ) : (
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => (
                              <p className="mb-6 leading-relaxed whitespace-pre-line">
                                {children}
                              </p>
                            ),
                          }}
                        >
                          {result}
                        </ReactMarkdown>
                      )}


                    </motion.div>
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center opacity-30 grayscale space-y-4">
                      <img src={dollarcityLogo} className="w-40" alt="Logo" />
                      <p className="font-bold text-[10px] uppercase tracking-[0.4em]">Engine Standby</p>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <div className="pt-2">
              {activeTab === 'chat' && (
                <div className="relative group">
                  <input 
                    type="text" 
                    value={question} 
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Escribe tu consulta..."
                    className="w-full bg-slate-100/50 border-2 border-slate-200 focus:border-[#00843D] focus:bg-white rounded-[2rem] px-8 py-6 pr-24 outline-none transition-all text-lg font-bold text-slate-800 placeholder:text-slate-400 shadow-inner"
                  />
                  
                  <button 
                    onClick={sendMessage}
                    disabled={!question || isTyping}
                    className="absolute right-3 top-1/2 -translate-y-1/2 bg-[#00843D] hover:bg-green-700 disabled:bg-slate-200 text-white p-5 rounded-[1.5rem] shadow-xl transition-all"
                  >
                    {loading ? <Loader2 className="animate-spin" size={24} /> : <Send size={24}/>}
                  </button>
                </div>
              )}

              </div>    

          </motion.div>
        </section>
      </main>

      <footer className="py-10 text-center">
        <div className="h-px bg-slate-200 max-w-sm mx-auto mb-6 opacity-30" />
        <p className="text-[11px] font-black text-slate-500 uppercase tracking-[0.6em]">
          © 2026 Dollarcity Intelligent Ops • Engine: <span className="text-[#00843D]">{aiModel}</span>
        </p>
      </footer>
    </div>
  );
};

export default App;