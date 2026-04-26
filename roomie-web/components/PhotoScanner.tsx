'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

type ScanIntent = 'add' | 'used' | 'general';

interface ScanResult {
  items: Array<{
    name: string;
    quantity?: number;
    unit?: string;
    confidence?: number;
  }>;
  intent: ScanIntent;
  message?: string;
}

export default function PhotoScanner() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [intent, setIntent] = useState<ScanIntent>('general');
  const [result, setResult] = useState<ScanResult | null>(null);

  const scanMutation = useMutation({
    mutationFn: async ({ image, scanIntent }: { image: string; scanIntent: ScanIntent }) => {
      const message = scanIntent === 'add'
        ? 'scan fridge and add items'
        : scanIntent === 'used'
          ? 'scan what I used'
          : 'scan fridge';

      const base64Data = image.split(',')[1];

      return alfredClient.sendMessage(
        message,
        'web-user',
        'iris',
        base64Data
      );
    },
    onSuccess: (data) => {
      try {
        const response = typeof data.result === 'string'
          ? JSON.parse(data.result)
          : data.result;
        setResult(response);
      } catch {
        setResult({
          items: [],
          intent,
          message: data.result || data.message || 'Scan complete',
        });
      }
    },
    onError: (error: any) => {
      setResult({
        items: [],
        intent,
        message: `Error: ${error.message || 'Failed to scan. Is Alfred running?'}`,
      });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    setSelectedFile(file);
    setResult(null);

    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleScan = () => {
    if (!preview) return;
    scanMutation.mutate({ image: preview, scanIntent: intent });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleAddToInventory = async () => {
    if (!result?.items || result.items.length === 0) return;

    try {
      for (const item of result.items) {
        await fetch('http://localhost:8000/inventory/fridge', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: item.name,
            quantity: item.quantity || 1,
            unit: item.unit || 'units',
            storage_location: 'fridge',
            category: 'scanned',
          }),
        });
      }

      alert(`✅ Added ${result.items.length} items to inventory!`);
      setResult(null);
      setPreview(null);
      setSelectedFile(null);
    } catch (err) {
      alert('❌ Failed to add items. Please try again.');
      console.error('Add to inventory error:', err);
    }
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <div style={{ fontSize: '36px', marginBottom: '12px' }}>📸</div>
        <div style={{ fontSize: '20px', fontWeight: '300', color: '#fff', marginBottom: '8px' }}>
          Fridge Scanner
        </div>
        <div style={{ fontSize: '11px', color: '#666' }}>
          Powered by Iris 👁️ • Upload a photo and select what you want to do
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Left Column: Upload & Intent */}
        <div>
          {/* Upload Area */}
          <div className="card" style={{ padding: '24px', marginBottom: '20px' }}>
            <div style={{
              fontSize: '10px',
              color: '#666',
              letterSpacing: '0.1em',
              marginBottom: '16px'
            }}>
              UPLOAD PHOTO
            </div>

            {!preview ? (
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                style={{
                  border: '2px dashed #2a2a2a',
                  borderRadius: '8px',
                  padding: '40px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => e.currentTarget.style.borderColor = '#444'}
                onMouseOut={(e) => e.currentTarget.style.borderColor = '#2a2a2a'}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>
                  Click to upload or drag & drop
                </div>
                <div style={{ fontSize: '10px', color: '#555' }}>
                  PNG, JPG up to 10MB
                </div>
                <input
                  id="file-input"
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
              </div>
            ) : (
              <div>
                <img
                  src={preview}
                  alt="Preview"
                  style={{
                    width: '100%',
                    borderRadius: '8px',
                    marginBottom: '12px',
                  }}
                />
                <button
                  onClick={() => {
                    setPreview(null);
                    setSelectedFile(null);
                    setResult(null);
                  }}
                  style={{
                    background: '#1a1a1a',
                    color: '#888',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '8px 16px',
                    fontSize: '10px',
                    cursor: 'pointer',
                    width: '100%',
                  }}
                >
                  REMOVE PHOTO
                </button>
              </div>
            )}
          </div>

          {/* Intent Selection */}
          {preview && (
            <div className="card" style={{ padding: '24px', marginBottom: '20px' }}>
              <div style={{
                fontSize: '10px',
                color: '#666',
                letterSpacing: '0.1em',
                marginBottom: '16px'
              }}>
                WHAT ARE YOU DOING?
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { id: 'add', label: 'Adding Items', desc: 'Just bought groceries, add to inventory', emoji: '➕', color: '#22c55e' },
                  { id: 'used', label: 'Used Items', desc: 'Cooked something, subtract from inventory', emoji: '➖', color: '#f59e0b' },
                  { id: 'general', label: 'General Scan', desc: 'Just checking what\'s there', emoji: '👀', color: '#60a5fa' },
                ].map(option => (
                  <label
                    key={option.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '16px',
                      background: intent === option.id ? `${option.color}22` : '#0a0a0a',
                      border: `1px solid ${intent === option.id ? option.color : '#1e1e1e'}`,
                      borderRadius: '6px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <input
                      type="radio"
                      name="intent"
                      value={option.id}
                      checked={intent === option.id}
                      onChange={(e) => setIntent(e.target.value as ScanIntent)}
                      style={{ accentColor: option.color }}
                    />
                    <span style={{ fontSize: '24px' }}>{option.emoji}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '11px', fontWeight: '500', color: '#fff', marginBottom: '4px' }}>
                        {option.label}
                      </div>
                      <div style={{ fontSize: '9px', color: '#888' }}>
                        {option.desc}
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              <button
                onClick={handleScan}
                disabled={scanMutation.isPending}
                style={{
                  background: intent === 'add' ? '#22c55e' : intent === 'used' ? '#f59e0b' : '#60a5fa',
                  color: '#000',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '12px 24px',
                  fontSize: '11px',
                  fontWeight: '500',
                  letterSpacing: '0.08em',
                  cursor: scanMutation.isPending ? 'not-allowed' : 'pointer',
                  width: '100%',
                  marginTop: '16px',
                }}
              >
                {scanMutation.isPending ? 'SCANNING...' : 'SCAN NOW'}
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Results */}
        <div>
          {result ? (
            <div className="fade-in">
              <div className="card" style={{
                padding: '24px',
                borderColor: intent === 'add' ? '#22c55e' : intent === 'used' ? '#f59e0b' : '#60a5fa'
              }}>
                <div style={{
                  fontSize: '10px',
                  color: '#666',
                  letterSpacing: '0.1em',
                  marginBottom: '16px'
                }}>
                  SCAN RESULTS
                </div>

                {result.message && (
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #1e1e1e',
                    borderRadius: '6px',
                    padding: '16px',
                    marginBottom: '16px',
                  }}>
                    <div style={{ fontSize: '11px', color: '#ccc', lineHeight: '1.5' }}>
                      {result.message}
                    </div>
                  </div>
                )}

                {result.items.length > 0 ? (
                  <div>
                    <div style={{
                      fontSize: '10px',
                      color: '#888',
                      marginBottom: '12px'
                    }}>
                      Detected {result.items.length} item{result.items.length !== 1 ? 's' : ''}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {result.items.map((item, i) => (
                        <div
                          key={i}
                          style={{
                            background: '#0a0a0a',
                            border: '1px solid #1e1e1e',
                            borderRadius: '4px',
                            padding: '12px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                        >
                          <div>
                            <div style={{ fontSize: '11px', color: '#fff', marginBottom: '2px' }}>
                              {item.name}
                            </div>
                            {item.quantity && (
                              <div style={{ fontSize: '9px', color: '#666' }}>
                                {item.quantity} {item.unit || 'units'}
                              </div>
                            )}
                          </div>
                          {item.confidence && (
                            <div style={{
                              fontSize: '9px',
                              color: item.confidence > 0.8 ? '#22c55e' : '#f59e0b',
                              background: item.confidence > 0.8 ? '#22c55e22' : '#f59e0b22',
                              padding: '4px 8px',
                              borderRadius: '3px',
                            }}>
                              {Math.round(item.confidence * 100)}% confident
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* ADD TO INVENTORY BUTTON */}
                    {intent !== 'general' && (
                      <button
                        onClick={handleAddToInventory}
                        style={{
                          width: '100%',
                          marginTop: '16px',
                          padding: '12px',
                          background: '#22c55e',
                          color: '#000',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '500',
                          letterSpacing: '0.08em',
                          cursor: 'pointer',
                        }}
                      >
                        ADD TO INVENTORY
                      </button>
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                    <div style={{ fontSize: '48px', marginBottom: '12px' }}>🤷</div>
                    <div style={{ fontSize: '11px' }}>
                      No items detected. Try a clearer photo.
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
              <div style={{ fontSize: '64px', marginBottom: '16px', opacity: 0.3 }}>👁️</div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                Iris is ready to scan
              </div>
              <div style={{ fontSize: '10px', color: '#444' }}>
                Upload a photo and select your intent to begin
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="card" style={{ padding: '20px', marginTop: '20px' }}>
        <div style={{
          fontSize: '10px',
          color: '#666',
          letterSpacing: '0.1em',
          marginBottom: '12px'
        }}>
          TIPS FOR BEST RESULTS
        </div>
        <ul style={{
          margin: 0,
          paddingLeft: '20px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
        }}>
          {[
            'Good lighting is key',
            'Clear view of labels',
            'Open fridge/cabinet doors fully',
            'Avoid blurry photos',
            'One shelf at a time works best',
            'Keep items in focus',
          ].map((tip, i) => (
            <li key={i} style={{ fontSize: '10px', color: '#888' }}>
              {tip}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}