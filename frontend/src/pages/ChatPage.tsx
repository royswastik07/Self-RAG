import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chat, getDatasets } from '../services/api';
import { Send, Bot, User, BrainCircuit, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [selectedDataset, setSelectedDataset] = useState<number | undefined>(undefined);
  const [selectedMessageIdx, setSelectedMessageIdx] = useState<number | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: getDatasets });

  const chatMutation = useMutation({
    mutationFn: (query: string) => chat(query, selectedDataset, messages.length > 0 ? messages[0].session_id : undefined),
    onSuccess: (data) => {
      setMessages(prev => {
        const newMsgs = [...prev];
        // Find the loading message and update it
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg.isLoading) {
          lastMsg.isLoading = false;
          lastMsg.content = data.answer;
          lastMsg.sources = data.sources;
          lastMsg.reflections = data.reflections;
        }
        return newMsgs;
      });
      setSelectedMessageIdx(messages.length); // Select the newly updated AI message
    },
    onError: () => {
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg.isLoading) {
          lastMsg.isLoading = false;
          lastMsg.content = "Sorry, an error occurred while generating the response.";
        }
        return newMsgs;
      });
    }
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [
      ...prev,
      { role: 'user', content: input },
      { role: 'assistant', content: '', isLoading: true }
    ]);
    chatMutation.mutate(input);
    setInput('');
  };

  const selectedAiMessage = selectedMessageIdx !== null ? messages[selectedMessageIdx] : null;

  return (
    <div className="flex h-full p-4 gap-4 relative">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col gap-4 max-w-4xl mx-auto w-full">
        <div className="glass-panel p-4 flex justify-between items-center z-10 shrink-0">
          <h2 className="text-xl font-bold text-slate-800">Chat</h2>
          <select 
            className="bg-white/50 border border-slate-200 rounded-lg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500/20"
            value={selectedDataset || ''}
            onChange={(e) => setSelectedDataset(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">All Datasets</option>
            {datasets?.map((ds: any) => (
              <option key={ds.id} value={ds.id}>{ds.name}</option>
            ))}
          </select>
        </div>

        <div className="glass-panel flex-1 flex flex-col overflow-hidden relative">
          <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-4">
                <Bot className="w-16 h-16 opacity-20" />
                <p>Ask a question based on your documents...</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center shrink-0 shadow-md">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                    msg.role === 'user' 
                      ? 'bg-slate-900 text-white shadow-md rounded-br-none'
                      : `bg-white/60 border border-white/40 shadow-sm rounded-bl-none cursor-pointer transition-all hover:bg-white/80 ${selectedMessageIdx === idx ? 'ring-2 ring-emerald-400' : ''}`
                  }`}
                  onClick={() => msg.role === 'assistant' && setSelectedMessageIdx(idx)}
                  >
                    {msg.isLoading ? (
                      <div className="flex items-center gap-2 text-emerald-600 font-medium">
                        <BrainCircuit className="w-5 h-5 animate-pulse" />
                        Thinking & Reflecting...
                      </div>
                    ) : (
                      <div className="prose prose-slate prose-sm max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                        {msg.reflections && (
                          <div className="mt-3 pt-3 border-t border-slate-200/50 flex gap-2 items-center text-xs font-medium text-slate-500">
                            {msg.reflections[msg.reflections.length - 1].is_supported ? (
                              <span className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">
                                <CheckCircle2 className="w-3.5 h-3.5" /> Grounded ({Math.round(msg.reflections[msg.reflections.length - 1].confidence * 100)}%)
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded-md">
                                <AlertCircle className="w-3.5 h-3.5" /> Insufficient Evidence
                              </span>
                            )}
                            <span className="flex items-center gap-1 bg-slate-100 px-2 py-1 rounded-md text-slate-600">
                              <BrainCircuit className="w-3.5 h-3.5" /> {msg.reflections.length} Reflection(s)
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-white/40 border-t border-white/20 backdrop-blur-md">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your documents..."
                disabled={chatMutation.isPending}
                className="flex-1 rounded-xl border border-slate-200 bg-white/80 px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all shadow-inner disabled:opacity-50"
              />
              <button 
                type="submit" 
                disabled={chatMutation.isPending || !input.trim()}
                className="bg-slate-900 text-white p-3 rounded-xl hover:bg-slate-800 transition-all shadow-md disabled:opacity-50 flex items-center justify-center w-12"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Side Panel: Reflection & Sources */}
      <div className={`w-96 shrink-0 transition-all duration-300 ${selectedAiMessage ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8 pointer-events-none absolute right-4 h-full'}`}>
        <div className="glass-panel h-full flex flex-col overflow-hidden">
          <div className="p-4 border-b border-white/20 bg-white/40 backdrop-blur-md sticky top-0 z-10 flex justify-between items-center">
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-emerald-500" />
              Self-RAG Logs
            </h3>
            <button onClick={() => setSelectedMessageIdx(null)} className="text-slate-400 hover:text-slate-600">×</button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-6">
            {selectedAiMessage?.reflections?.map((ref: any, i: number) => (
              <div key={i} className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                  <div className="h-px flex-1 bg-slate-200" />
                  Iteration {ref.iteration}
                  <div className="h-px flex-1 bg-slate-200" />
                </div>
                
                {ref.new_query && (
                  <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-3 text-sm">
                    <span className="font-semibold text-blue-700 block mb-1">Rewritten Query:</span>
                    <span className="text-slate-700 italic">"{ref.new_query}"</span>
                  </div>
                )}

                <div className={`rounded-lg p-3 text-sm border ${ref.is_supported ? 'bg-emerald-50/50 border-emerald-100' : 'bg-amber-50/50 border-amber-100'}`}>
                  <div className="flex justify-between items-center mb-2">
                    <span className={`font-semibold ${ref.is_supported ? 'text-emerald-700' : 'text-amber-700'}`}>Reflection Verdict</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-white shadow-sm border border-slate-100">
                      Conf: {Math.round(ref.confidence * 100)}%
                    </span>
                  </div>
                  <p className="text-slate-600 text-xs leading-relaxed">{ref.reason}</p>
                  {!ref.is_supported && ref.retrieve_again && (
                    <div className="mt-2 text-amber-700 font-medium text-xs flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5" /> Decided to re-retrieve
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1">
                    <FileText className="w-3.5 h-3.5" /> Retrieved Chunks ({ref.retrieved_chunks.length})
                  </span>
                  {ref.retrieved_chunks.map((chunk: any, j: number) => (
                    <div key={j} className="bg-white/60 border border-slate-100 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-1 gap-2">
                        <span className="text-xs font-bold text-slate-700 truncate">{chunk.file_name}</span>
                        <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded whitespace-nowrap">Score: {chunk.confidence_score.toFixed(3)}</span>
                      </div>
                      <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed">{chunk.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
