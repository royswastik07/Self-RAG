import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDatasets, createDataset, uploadDocument, deleteDataset } from '../services/api';
import { Upload, Plus, FileText, Loader2, Database, Trash2 } from 'lucide-react';

export default function DatasetsPage() {
  const queryClient = useQueryClient();
  const [newDatasetName, setNewDatasetName] = useState('');
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);

  // Advanced Ingestion Configuration State
  const [chunkSize, setChunkSize] = useState<number>(1000);
  const [chunkOverlap, setChunkOverlap] = useState<number>(200);
  const [chunkMethod, setChunkMethod] = useState<string>('recursive');
  const [embeddingModel, setEmbeddingModel] = useState<string>('BAAI/bge-small-en-v1.5');

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: getDatasets,
  });

  const createMutation = useMutation({
    mutationFn: createDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setNewDatasetName('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDataset,
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      if (selectedDataset === deletedId) {
        setSelectedDataset(null);
      }
    },
    onError: () => {
      alert('Failed to delete dataset.');
    }
  });

  const uploadMutation = useMutation({
    mutationFn: ({ id, file, options }: { id: number, file: File, options: any }) => uploadDocument(id, file, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      alert('File uploaded successfully!');
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || error.message || 'Failed to upload file.';
      alert(`Upload Failed: ${msg}`);
    }
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (chunkOverlap >= chunkSize) {
      alert(`Chunk Overlap (${chunkOverlap}) must be strictly smaller than Chunk Size (${chunkSize}).`);
      e.target.value = '';
      return;
    }

    if (e.target.files && e.target.files.length > 0 && selectedDataset) {
      uploadMutation.mutate({ 
        id: selectedDataset, 
        file: e.target.files[0],
        options: {
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap,
          chunk_method: chunkMethod,
          embedding_model: embeddingModel
        }
      });
    }
  };

  return (
    <div className="p-8 h-full flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-slate-800">Datasets</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Left Column: Dataset List */}
        <div className="glass-panel p-6 flex flex-col gap-4">
          <div className="flex gap-2">
            <input
              type="text"
              className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
              placeholder="New dataset name..."
              value={newDatasetName}
              onChange={(e) => setNewDatasetName(e.target.value)}
            />
            <button
              onClick={() => createMutation.mutate(newDatasetName)}
              disabled={!newDatasetName || createMutation.isPending}
              className="bg-slate-900 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 hover:bg-slate-800 disabled:opacity-50 transition-colors"
            >
              {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-2">
            {isLoading ? (
              <div className="flex justify-center p-4"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>
            ) : (
              datasets?.map((ds: any) => (
                <div
                  key={ds.id}
                  onClick={() => setSelectedDataset(ds.id)}
                  className={`p-4 rounded-xl cursor-pointer border transition-all flex justify-between items-center group ${
                    selectedDataset === ds.id
                      ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                      : 'border-slate-100 hover:border-slate-300 hover:bg-white/50'
                  }`}
                >
                  <div>
                    <h3 className="font-semibold text-slate-800">{ds.name}</h3>
                    <div className="text-xs text-slate-500 flex gap-4 mt-2">
                      <span>{ds.document_count} docs</span>
                      <span>{ds.chunk_count} chunks</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm(`Are you sure you want to delete "${ds.name}"? This will delete all its documents, chunks, and vector data permanently.`)) {
                        deleteMutation.mutate(ds.id);
                      }
                    }}
                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                    title="Delete dataset"
                  >
                    {deleteMutation.isPending && deleteMutation.variables === ds.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Upload Area */}
        <div className="glass-panel lg:col-span-2 p-6 flex flex-col gap-4 items-center justify-center">
          {selectedDataset ? (
            <div className="text-center flex flex-col items-center gap-4 max-w-md w-full">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-2">
                <Upload className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-800">Upload to Dataset</h3>
              <p className="text-slate-500 text-sm mb-4">
                Supported formats: PDF, DOCX, TXT, MD
              </p>
              <label className="w-full relative">
                <input 
                  type="file" 
                  className="hidden" 
                  accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.html"
                  onChange={handleFileUpload}
                  disabled={uploadMutation.isPending}
                />
                <div className={`w-full p-4 border-2 border-dashed border-slate-300 rounded-xl cursor-pointer hover:bg-slate-50 transition-colors flex items-center justify-center gap-2 text-slate-600 font-medium ${uploadMutation.isPending ? 'opacity-50 pointer-events-none' : ''}`}>
                  {uploadMutation.isPending ? (
                    <><Loader2 className="w-5 h-5 animate-spin" /> Uploading & Indexing...</>
                  ) : (
                    <><FileText className="w-5 h-5" /> Select File</>
                  )}
                </div>
              </label>

              {/* Advanced Configuration */}
              <div className="w-full mt-4 text-left border-t border-slate-200 pt-4">
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Advanced Ingestion Settings</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-slate-500">Chunk Size</label>
                    <input type="number" value={chunkSize} onChange={e => setChunkSize(parseInt(e.target.value) || 1000)} className="rounded-md border border-slate-200 px-3 py-1.5 text-sm" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-slate-500">Chunk Overlap</label>
                    <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(parseInt(e.target.value) || 200)} className="rounded-md border border-slate-200 px-3 py-1.5 text-sm" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-slate-500">Chunking Method</label>
                    <select value={chunkMethod} onChange={e => setChunkMethod(e.target.value)} className="rounded-md border border-slate-200 px-3 py-1.5 text-sm bg-white">
                      <option value="recursive">Recursive Character</option>
                      <option value="character">Standard Character</option>
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-slate-500">Embedding Model</label>
                    <select value={embeddingModel} onChange={e => setEmbeddingModel(e.target.value)} className="rounded-md border border-slate-200 px-3 py-1.5 text-sm bg-white">
                      <option value="BAAI/bge-small-en-v1.5">BGE Small (Fast)</option>
                      <option value="sentence-transformers/all-MiniLM-L6-v2">MiniLM-L6-v2 (Very Fast)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400 flex flex-col items-center gap-4">
              <Database className="w-12 h-12 opacity-20" />
              <p>Select a dataset to manage files</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
