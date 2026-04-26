'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

interface Message {
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  agent?: string;
}

const AGENT_INFO = {
  alfred: { name: 'Alfred', emoji: '🎩', color: '#60a5fa' },
  elsa: { name: 'Elsa', emoji: '❄️', color: '#22c55e' },
  remy: { name: 'Remy', emoji: '👨‍🍳', color: '#f59e0b' },
  lebowski: { name: 'Lebowski', emoji: '🥃', color: '#a78bfa' },
  finn: { name: 'Finn', emoji: '🎯', color: '#ec4899' },
  iris: { name: 'Iris', emoji: '👁️', color: '#8b5cf6' },
};

interface AgentChatProps {
  agentId: string;
}

export default function AgentChat({ agentId }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const agent = AGENT_INFO[agentId as keyof typeof AGENT_INFO];

  const sendMessageMutation = useMutation({
    mutationFn: (message: string) =>
      alfredClient.sendMessage(message, 'web-user', agentId),
    onSuccess: (data, variables) => {
      // Add user message
      setMessages(prev => [...prev, {
        role: 'user',
        content: variables,
        timestamp: new Date(),
      }]);

      // Add agent response - backend returns 'result' not 'response'
      const responseContent = typeof data.result === 'string'
        ? data.result
        : typeof data.message === 'string'
          ? data.message
          : JSON.stringify(data.result || data);

      setMessages(prev => [...prev, {
        role: 'agent',
        content: data.result || data.message || 'No response',
        timestamp: new Date(),
        agent: agentId,
      }]);

      setInput('');
    },
    onError: (error: any) => {
      // Show error message in chat
      setMessages(prev => [...prev, {
        role: 'agent',
        content: `Error: ${error.message || 'Failed to send message. Is Alfred running?'}`,
        timestamp: new Date(),
        agent: agentId,
      }]);
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessageMutation.mutate(input.trim());
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 200px)',
      maxHeight: '700px'
    }}>
      {/* Chat Header */}
      <div className="card" style={{
        padding: '16px',
        marginBottom: '12px',
        borderColor: agent.color,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '32px' }}>{agent.emoji}</span>
          <div>
            <div style={{ fontSize: '16px', fontWeight: '500', color: '#fff' }}>
              Chat with {agent.name}
            </div>
            <div style={{ fontSize: '10px', color: agent.color, letterSpacing: '0.1em' }}>
              {agentId.toUpperCase()}
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="card" style={{
        flex: 1,
        padding: '20px',
        overflowY: 'auto',
        marginBottom: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}>
        {messages.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#666'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>
              {agent.emoji}
            </div>
            <div style={{ fontSize: '12px', marginBottom: '8px' }}>
              Start a conversation with {agent.name}
            </div>
            <div style={{ fontSize: '10px', color: '#444' }}>
              Try: "What can you do?" or "Help me"
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '70%',
            }}
          >
            <div
              style={{
                background: msg.role === 'user' ? '#1a1a1a' : `${agent.color}22`,
                border: `1px solid ${msg.role === 'user' ? '#2a2a2a' : `${agent.color}44`}`,
                borderRadius: '8px',
                padding: '12px 16px',
              }}
            >
              <div style={{
                fontSize: '9px',
                color: '#666',
                marginBottom: '6px',
                letterSpacing: '0.05em'
              }}>
                {msg.role === 'user' ? 'YOU' : agent.name.toUpperCase()} · {msg.timestamp.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div style={{
                fontSize: '11px',
                color: '#e8e8e8',
                lineHeight: '1.5',
                whiteSpace: 'pre-wrap'
              }}>
                {typeof msg.content === 'object'
                  ? JSON.stringify(msg.content, null, 2)  // Convert object to string
                  : msg.content}
              </div>
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="card" style={{ padding: '16px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={`Message ${agent.name}...`}
            disabled={sendMessageMutation.isPending}
            style={{
              flex: 1,
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '4px',
              padding: '12px',
              color: '#e8e8e8',
              fontSize: '11px',
              fontFamily: 'inherit',
              resize: 'none',
              minHeight: '60px',
              maxHeight: '120px',
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMessageMutation.isPending}
            style={{
              background: input.trim() && !sendMessageMutation.isPending ? agent.color : '#1a1a1a',
              color: input.trim() && !sendMessageMutation.isPending ? '#000' : '#444',
              border: 'none',
              borderRadius: '4px',
              padding: '12px 24px',
              fontSize: '11px',
              fontWeight: '500',
              letterSpacing: '0.08em',
              cursor: input.trim() && !sendMessageMutation.isPending ? 'pointer' : 'not-allowed',
              whiteSpace: 'nowrap',
            }}
          >
            {sendMessageMutation.isPending ? 'SENDING...' : 'SEND'}
          </button>
        </div>
        <div style={{
          fontSize: '9px',
          color: '#444',
          marginTop: '8px',
          textAlign: 'center'
        }}>
          Press Enter to send • Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}
