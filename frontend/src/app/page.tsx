'use client';

import React, { useState, useEffect } from 'react';

interface CloneOptions {
  include_images: boolean;
  include_fonts: boolean;
  mobile_responsive: boolean;
  extract_colors: boolean;
  max_wait_time: number;
  viewport_width: number;
  viewport_height: number;
  // New Agentic Cloner options
  target_style: 'modern' | 'minimal' | 'corporate' | 'creative';
  include_animations: boolean;
  mobile_first: boolean;
}

interface CloneStatus {
  id: string;
  status: 'pending' | 'scraping' | 'processing' | 'generating' | 'complete' | 'error';
  progress: number;
  message?: string;
  created_at: string;
  updated_at: string;
}

interface PrecisionMetrics {
  overall_precision: number;
  structure_similarity: number;
  content_similarity: number;
  styling_similarity: number;
  semantic_similarity: number;
  layout_similarity: number;
  confidence: 'low' | 'medium' | 'high';
}

interface CloneResult {
  id: string;
  status: 'complete' | 'error';
  original_url: string;
  generated_html?: string;
  generated_css?: string;
  preview_url?: string;
  error_message?: string;
  processing_time?: number;
  similarity_score?: number;
  precision_metrics?: PrecisionMetrics;
}

const API_BASE = 'http://localhost:8000';

export default function Home() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<CloneStatus | null>(null);
  const [result, setResult] = useState<CloneResult | null>(null);
  const [showOptions, setShowOptions] = useState(false);
  const [useAgenticCloner, setUseAgenticCloner] = useState(true);
  const [options, setOptions] = useState<CloneOptions>({
    include_images: true,
    include_fonts: true,
    mobile_responsive: true,
    extract_colors: true,
    max_wait_time: 30,
    viewport_width: 1920,
    viewport_height: 1080,
    // New Agentic Cloner options
    target_style: 'modern',
    include_animations: true,
    mobile_first: true,
  });

  // Poll for job status
  useEffect(() => {
    if (!currentJob) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/clone/${currentJob}`);
        if (response.ok) {
          const status: CloneStatus = await response.json();
          setJobStatus(status);

          if (status.status === 'complete') {
            // Fetch the result
            const resultResponse = await fetch(`${API_BASE}/api/clone/${currentJob}/result`);
            if (resultResponse.ok) {
              const resultData: CloneResult = await resultResponse.json();
              setResult(resultData);
            }
            setIsLoading(false);
          } else if (status.status === 'error') {
            setIsLoading(false);
          }
        }
      } catch (error) {
        console.error('Failed to poll status:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, [currentJob]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) return;

    setIsLoading(true);
    setCurrentJob(null);
    setJobStatus(null);
    setResult(null);

    try {
      const endpoint = useAgenticCloner ? '/api/agentic-clone' : '/api/clone';
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          options,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        if (useAgenticCloner) {
          // Agentic cloner returns result directly
          if (data.success) {
            setResult({
              id: data.id,
              status: 'complete',
              original_url: url.trim(),
              generated_html: data.html,
              preview_url: data.preview_url,
              processing_time: data.processing_time
            });
          } else {
            alert(`Error: ${data.message || 'Agentic clone failed'}`);
          }
          setIsLoading(false);
        } else {
          // Standard cloner returns job ID for polling
          setCurrentJob(data.id);
        }
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || error.message || 'Failed to start clone job'}`);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Clone request failed:', error);
      alert('Failed to start clone job. Please try again.');
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setUrl('');
    setIsLoading(false);
    setCurrentJob(null);
    setJobStatus(null);
    setResult(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'processing':
      case 'generating': return 'text-blue-600';
      case 'scraping': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'pending': return 'Initializing...';
      case 'scraping': return 'Analyzing website structure...';
      case 'processing': return 'Processing design elements...';
      case 'generating': return 'Generating HTML with AI...';
      case 'complete': return 'Clone completed successfully!';
      case 'error': return 'Clone failed';
      default: return status;
    }
  };

  const interpretScore = (score: number): { label: string; color: string; emoji: string } => {
    if (score >= 0.9) return { label: 'Excellent', color: 'text-green-600', emoji: '🎯' };
    if (score >= 0.8) return { label: 'Very Good', color: 'text-green-500', emoji: '✅' };
    if (score >= 0.7) return { label: 'Good', color: 'text-blue-600', emoji: '👍' };
    if (score >= 0.6) return { label: 'Fair', color: 'text-yellow-600', emoji: '⚠️' };
    if (score >= 0.4) return { label: 'Poor', color: 'text-orange-600', emoji: '📉' };
    return { label: 'Very Poor', color: 'text-red-600', emoji: '❌' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            🌐 Website Cloner
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI-powered website cloning using advanced web scraping and machine learning.
            Enter any website URL and watch our AI recreate it with modern HTML & CSS.
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Cloner Type Toggle */}
          <div className="bg-white rounded-lg shadow-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-800">
                  {useAgenticCloner ? '🤖 Agentic Cloner v0.1' : '🔧 Standard Cloner'}
                </h3>
                <p className="text-sm text-gray-600">
                  {useAgenticCloner 
                    ? 'AI-powered cloning with memory and style intelligence'
                    : 'Traditional web scraping and HTML generation'
                  }
                </p>
              </div>
              <label className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">Standard</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={useAgenticCloner}
                    onChange={(e) => setUseAgenticCloner(e.target.checked)}
                    className="sr-only"
                    disabled={isLoading}
                  />
                  <div 
                    className={`w-12 h-6 rounded-full transition-colors cursor-pointer ${
                      useAgenticCloner ? 'bg-purple-600' : 'bg-gray-300'
                    }`}
                    onClick={() => !isLoading && setUseAgenticCloner(!useAgenticCloner)}
                  >
                    <div 
                      className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                        useAgenticCloner ? 'translate-x-6' : 'translate-x-0.5'
                      } mt-0.5`}
                    />
                  </div>
                </div>
                <span className="text-sm text-gray-600">Agentic</span>
              </label>
            </div>
          </div>

          {/* Input Form */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                  Website URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    id="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-black"
                    required
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowOptions(!showOptions)}
                    className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    disabled={isLoading}
                  >
                    ⚙️ Options
                  </button>
                </div>
              </div>

              {/* Advanced Options */}
              {showOptions && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <h3 className="font-medium text-gray-800">Clone Options</h3>
                  
                  {/* Style Options */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Target Style</label>
                    <select
                      value={options.target_style}
                      onChange={(e) => setOptions({...options, target_style: e.target.value as any})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="modern">🚀 Modern - Clean lines, bold typography, vibrant colors</option>
                      <option value="minimal">✨ Minimal - Maximum white space, limited colors</option>
                      <option value="corporate">🏢 Corporate - Professional blues/grays, structured</option>
                      <option value="creative">🎨 Creative - Bold colors, unique layouts, animations</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.include_images}
                        onChange={(e) => setOptions({...options, include_images: e.target.checked})}
                        className="rounded"
                      />
                      <span className="text-sm">Include Images</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.include_fonts}
                        onChange={(e) => setOptions({...options, include_fonts: e.target.checked})}
                        className="rounded"
                      />
                      <span className="text-sm">Include Fonts</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.mobile_responsive}
                        onChange={(e) => setOptions({...options, mobile_responsive: e.target.checked})}
                        className="rounded"
                      />
                      <span className="text-sm">Mobile Responsive</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.extract_colors}
                        onChange={(e) => setOptions({...options, extract_colors: e.target.checked})}
                        className="rounded"
                      />
                      <span className="text-sm">Extract Colors</span>
                    </label>

                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.include_animations}
                        onChange={(e) => setOptions({...options, include_animations: e.target.checked})}
                        className="rounded"
                      />
                      <span className="text-sm">Include Animations</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={options.mobile_first}
                        onChange={(e) => setOptions({...options, mobile_first: e.target.checked})}
                        className="rounded"
                      />
                      <span className="text-sm">Mobile First Design</span>
                    </label>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Max Wait Time (seconds)</label>
                      <input
                        type="number"
                        value={options.max_wait_time}
                        onChange={(e) => setOptions({...options, max_wait_time: parseInt(e.target.value) || 30})}
                        min="5"
                        max="120"
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Viewport Width</label>
                      <select
                        value={options.viewport_width}
                        onChange={(e) => setOptions({...options, viewport_width: parseInt(e.target.value)})}
                        className="w-full px-2 py-1 border rounded text-sm"
                      >
                        <option value={1920}>Desktop (1920px)</option>
                        <option value={1366}>Laptop (1366px)</option>
                        <option value={768}>Tablet (768px)</option>
                        <option value={375}>Mobile (375px)</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={isLoading || !url.trim()}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isLoading 
                    ? (useAgenticCloner ? '🤖 AI Cloning...' : '🚀 Cloning...') 
                    : (useAgenticCloner ? '🤖 AI Clone Website' : '🎯 Clone Website')
                  }
                </button>
                
                {(isLoading || result) && (
                  <button
                    type="button"
                    onClick={handleReset}
                    className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    Reset
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Status Display */}
          {jobStatus && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Cloning Progress</h2>
                <span className={`text-sm font-medium ${getStatusColor(jobStatus.status)}`}>
                  {getStatusMessage(jobStatus.status)}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-purple-600 to-blue-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${jobStatus.progress}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Job ID: {jobStatus.id}</span>
                  <span>{jobStatus.progress}% complete</span>
                </div>
                
                {jobStatus.message && (
                  <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                    {jobStatus.message}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Results Display */}
          {result && result.status === 'complete' && (
            <div className="space-y-6">
              {/* Precision Metrics Summary */}
              {result.precision_metrics && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <h2 className="text-xl font-semibold text-gray-800 mb-4">📊 Precision Analysis</h2>
                  
                  {/* Overall Score */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-medium text-gray-700">Overall Precision</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-lg font-bold ${interpretScore(result.precision_metrics.overall_precision).color}`}>
                          {interpretScore(result.precision_metrics.overall_precision).emoji} {Math.round(result.precision_metrics.overall_precision * 100)}%
                        </span>
                        <span className={`text-sm px-2 py-1 rounded ${interpretScore(result.precision_metrics.overall_precision).color} bg-opacity-10`}>
                          {interpretScore(result.precision_metrics.overall_precision).label}
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-1000 ${
                          result.precision_metrics.overall_precision >= 0.8 ? 'bg-green-500' :
                          result.precision_metrics.overall_precision >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${result.precision_metrics.overall_precision * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Detailed Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[
                      { key: 'structure_similarity', label: 'Structure', icon: '🏗️', description: 'HTML structure & hierarchy' },
                      { key: 'content_similarity', label: 'Content', icon: '📝', description: 'Text content preservation' },
                      { key: 'styling_similarity', label: 'Styling', icon: '🎨', description: 'CSS classes & styles' },
                      { key: 'semantic_similarity', label: 'Semantic', icon: '🏷️', description: 'HTML5 semantic elements' },
                      { key: 'layout_similarity', label: 'Layout', icon: '📐', description: 'Layout patterns' },
                    ].map((metric) => {
                      const score = result.precision_metrics![metric.key as keyof PrecisionMetrics] as number;
                      const interpretation = interpretScore(score);
                      
                      return (
                        <div key={metric.key} className="bg-gray-50 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{metric.icon}</span>
                              <span className="font-medium text-gray-700">{metric.label}</span>
                            </div>
                            <span className={`font-bold ${interpretation.color}`}>
                              {Math.round(score * 100)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                            <div 
                              className={`h-1.5 rounded-full transition-all duration-1000 ${
                                score >= 0.8 ? 'bg-green-500' :
                                score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${score * 100}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500">{metric.description}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Confidence & Stats */}
                  <div className="mt-6 flex items-center justify-between text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center gap-4">
                      <span>⏱️ Processing Time: {result.processing_time?.toFixed(1)}s</span>
                      <span className={`px-2 py-1 rounded ${
                        result.precision_metrics.confidence === 'high' ? 'bg-green-100 text-green-700' :
                        result.precision_metrics.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        📈 {result.precision_metrics.confidence.charAt(0).toUpperCase() + result.precision_metrics.confidence.slice(1)} Confidence
                      </span>
                    </div>
                    <span>Job ID: {result.id}</span>
                  </div>
                </div>
              )}

              {/* Clone Results */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-800">Clone Complete! 🎉</h2>
                <div className="flex gap-2 text-sm text-gray-600">
                    {!result.precision_metrics && result.processing_time && (
                    <span>⏱️ {result.processing_time.toFixed(1)}s</span>
                  )}
                    {!result.precision_metrics && result.similarity_score && (
                    <span>📊 {Math.round(result.similarity_score * 100)}% similar</span>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Preview */}
                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Live Preview</h3>
                  <div className="border rounded-lg overflow-hidden bg-gray-50">
                    {result.preview_url ? (
                      <>
                        <iframe
                          src={`${API_BASE}/api/preview-proxy?url=${encodeURIComponent(result.preview_url.startsWith('http') ? result.preview_url : `${API_BASE}${result.preview_url}`)}`}
                          className="w-full h-96"
                          title="Cloned Website Preview"
                          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                          onError={(e) => {
                            console.error('Iframe error:', e);
                            console.log('Preview URL:', result.preview_url);
                            // Fallback to direct URL if proxy fails
                            const iframe = e.target as HTMLIFrameElement;
                            const directUrl = result.preview_url!.startsWith('http') ? result.preview_url! : `${API_BASE}${result.preview_url!}`;
                            iframe.src = directUrl;
                          }}
                          onLoad={(e) => {
                            console.log('Iframe loaded successfully via proxy');
                          }}
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Preview served via proxy for better compatibility
                        </div>
                      </>
                    ) : (
                      <div className="h-96 flex items-center justify-center text-gray-500">
                        Preview not available
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-3 flex gap-2">
                    {result.preview_url && (
                      <a
                        href={`${API_BASE}/api/preview-proxy?url=${encodeURIComponent(result.preview_url.startsWith('http') ? result.preview_url : `${API_BASE}${result.preview_url}`)}`}
            target="_blank"
            rel="noopener noreferrer"
                        className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                      >
                        🔗 Open in New Tab
                      </a>
                    )}
                    
                    {result.preview_url && (
                      <button
                        onClick={() => {
                          const proxyUrl = `${API_BASE}/api/preview-proxy?url=${encodeURIComponent(result.preview_url!.startsWith('http') ? result.preview_url! : `${API_BASE}${result.preview_url!}`)}`;
                          console.log('Debug - Using proxy URL:', proxyUrl);
                          
                          // Create a new window with better preview handling
                          const previewWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
                          if (previewWindow) {
                            previewWindow.document.write(`
                              <html>
                                <head>
                                  <title>Preview: ${result.original_url}</title>
                                  <style>
                                    body { margin: 0; padding: 20px; font-family: system-ui; }
                                    .loading { text-align: center; padding: 50px; color: #666; }
                                    iframe { width: 100%; height: calc(100vh - 100px); border: 1px solid #ddd; border-radius: 4px; }
                                  </style>
                                </head>
                                <body>
                                  <div class="loading">Loading preview...</div>
                                  <iframe src="${proxyUrl}" onload="document.querySelector('.loading').style.display='none'"></iframe>
                                </body>
                              </html>
                            `);
                            previewWindow.document.close();
                          }
                        }}
                        className="px-4 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition-colors"
                      >
                        🪟 Enhanced Preview
                      </button>
                    )}
                    
                    {result.preview_url && (
                      <a
                        href={result.preview_url!.startsWith('http') ? result.preview_url! : `${API_BASE}${result.preview_url!}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                        title="Direct Supabase URL (may show raw HTML)"
                      >
                        🔗 Raw URL
                      </a>
                    )}
                    
                    <a
                      href={result.original_url}
            target="_blank"
            rel="noopener noreferrer"
                      className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
          >
                      👀 View Original
          </a>
        </div>
                </div>
                
                {/* Code */}
                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Generated Code</h3>
                  <div className="space-y-3">
                    {result.generated_html && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-600">HTML</span>
                          <button
                            onClick={() => navigator.clipboard.writeText(result.generated_html || '')}
                            className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                          >
                            📋 Copy
                          </button>
                        </div>
                        <textarea
                          value={result.generated_html}
                          readOnly
                          className="w-full h-32 text-xs font-mono p-3 border rounded bg-gray-50 resize-none text-black"
                        />
                      </div>
                    )}
                    
                    {result.generated_css && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-600">CSS</span>
                          <button
                            onClick={() => navigator.clipboard.writeText(result.generated_css || '')}
                            className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                          >
                            📋 Copy
                          </button>
                        </div>
                        <textarea
                          value={result.generated_css}
                          readOnly
                          className="w-full h-32 text-xs font-mono p-3 border rounded bg-gray-50 resize-none text-black"
                        />
                      </div>
                    )}
                  </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {result && result.status === 'error' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold text-red-600 mb-4">❌ Clone Failed</h2>
                <p className="text-gray-700 mb-4">{result.error_message}</p>
                <button
                  onClick={handleReset}
                  className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
                  Try Again
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500 text-sm">
          <p>Powered by OpenAI GPT-4o • Built with Next.js & FastAPI</p>
        </div>
      </div>
    </div>
  );
}
