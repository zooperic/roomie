'use client';

import { useQuery } from '@tanstack/react-query';
import { alfredClient } from '@/lib/alfred-client';

const AGENT_PROFILES = {
  alfred: {
    name: 'Alfred',
    emoji: '🎩',
    role: 'The Orchestrator',
    personality: 'British, formal, always composed',
    quote: '"Certainly, sir. I shall coordinate the household affairs."',
    color: '#60a5fa',
    quirks: [
      'Calls everyone "sir" or "madam"',
      'Never raises his voice',
      'Secretly judges your life choices',
      'Has a backup plan for everything',
    ],
    skills: [
      'Routing requests to agents',
      'Coordinating multi-agent tasks',
      'Keeping everyone in line',
      'Making you feel important',
    ],
    funFact: 'Once served tea to the Queen (in a parallel universe)',
  },
  elsa: {
    name: 'Elsa',
    emoji: '❄️',
    role: 'The Fridge Guardian',
    personality: 'Meticulous, slightly neurotic, cares deeply',
    quote: '"Your milk expires tomorrow. TOMORROW. How do you live like this?"',
    color: '#22c55e',
    quirks: [
      'Panics when things expire',
      'Knows exact quantity of everything',
      'Judges your leftovers',
      'Secretly proud of organization',
    ],
    skills: [
      'Tracking fridge inventory',
      'Low stock warnings',
      'Recipe ingredient checks',
      'Preventing food waste',
    ],
    funFact: 'Has memorized the expiry date of every item ever purchased',
  },
  remy: {
    name: 'Remy',
    emoji: '👨‍🍳',
    role: 'The Kitchen Master',
    personality: 'Passionate, creative, slightly pretentious',
    quote: '"Anyone can cook... but not with THAT pantry, mon ami."',
    color: '#f59e0b',
    quirks: [
      'Critiques your spice collection',
      'Dreams in recipes',
      'Gets emotional about basil',
      'Refuses to acknowledge instant noodles',
    ],
    skills: [
      'Recipe parsing (all formats)',
      'Pantry management',
      'Meal suggestions',
      'Making you feel uncultured',
    ],
    funFact: 'Once made ratatouille with only pantry staples. It was magnificent.',
  },
  lebowski: {
    name: 'Lebowski',
    emoji: '🥃',
    role: 'The Procurer',
    personality: 'Laid-back, resourceful, speaks Hinglish fluently',
    quote: '"The Dude abides... and gets your groceries, bro."',
    color: '#a78bfa',
    quirks: [
      'Calls everyone "bro" or "dude"',
      'Knows every delivery person by name',
      'Masters both English and Hindi slang',
      'Has opinions on every brand',
    ],
    skills: [
      'Catalog matching (33 products memorized)',
      'Swiggy integration',
      'Price negotiations (in his mind)',
      'Hinglish translation',
    ],
    funFact: 'Can find kasuri methi at 3am. Don\'t ask how.',
  },
  finn: {
    name: 'Finn',
    emoji: '🎯',
    role: 'The Strategist',
    personality: 'Analytical, data-driven, eerily accurate',
    quote: '"Based on your consumption patterns, you\'ll run out of coffee in 3.2 days."',
    color: '#ec4899',
    quirks: [
      'Predicts everything',
      'Loves spreadsheets',
      'Speaks in probabilities',
      'Knows you better than you know yourself',
    ],
    skills: [
      'Consumption pattern analysis',
      'Predictive ordering',
      'Usage tracking',
      'Making you feel predictable',
    ],
    funFact: 'Predicted you\'d forget milk 47 times. Was right 46 times.',
  },
  iris: {
    name: 'Iris',
    emoji: '👁️',
    role: 'The Observer',
    personality: 'Perceptive, visual, sees everything',
    quote: '"I see you\'ve rearranged the cheese. Again. Third time this week."',
    color: '#8b5cf6',
    quirks: [
      'Notices microscopic changes',
      'Remembers every photo taken',
      'Judges your organization skills',
      'Has perfect memory',
    ],
    skills: [
      'Image recognition',
      'Fridge scanning',
      'Visual inventory',
      'Silent judgment',
    ],
    funFact: 'Can identify 47 types of cheese just from photos. You have 2.',
  },
};

const AGENT_ORDER = ['alfred', 'elsa', 'remy', 'lebowski', 'finn', 'iris'];

export default function Roomies() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['alfred-status'],
    queryFn: () => alfredClient.getStatus(),
    refetchInterval: 30000, // 30 seconds instead of 10
  });

  if (isLoading) {
    return (
      <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '14px', color: '#666' }}>Loading roomies...</div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ fontSize: '36px', marginBottom: '12px' }}>👥</div>
        <div style={{ 
          fontSize: '24px', 
          fontWeight: '300', 
          color: '#fff',
          marginBottom: '8px'
        }}>
          Meet Your Roomies
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>
          The AI agents keeping your kitchen running
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '20px',
      }}>
        {AGENT_ORDER.map(agentId => {
          const agent = AGENT_PROFILES[agentId as keyof typeof AGENT_PROFILES];
          const agentStatus = status?.agents?.[agentId];
          const isHealthy = agentStatus?.healthy;

          return (
            <div 
              key={agentId}
              className="card"
              style={{ 
                padding: '24px',
                borderColor: isHealthy ? agent.color : '#1a1a1a',
                position: 'relative',
                transition: 'all 0.2s ease',
              }}
            >
              {/* Status Indicator */}
              <div style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: isHealthy ? agent.color : '#444',
                boxShadow: isHealthy ? `0 0 8px ${agent.color}` : 'none',
              }} />

              {/* Agent Header */}
              <div style={{ marginBottom: '20px' }}>
                <div style={{ 
                  fontSize: '48px', 
                  marginBottom: '12px',
                  textAlign: 'center'
                }}>
                  {agent.emoji}
                </div>
                <div style={{ 
                  fontSize: '18px', 
                  fontWeight: '500', 
                  color: '#fff',
                  textAlign: 'center',
                  marginBottom: '4px'
                }}>
                  {agent.name}
                </div>
                <div style={{ 
                  fontSize: '10px', 
                  color: agent.color,
                  textAlign: 'center',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase'
                }}>
                  {agent.role}
                </div>
              </div>

              {/* Personality */}
              <div style={{ 
                fontSize: '10px', 
                color: '#888',
                fontStyle: 'italic',
                marginBottom: '12px',
                textAlign: 'center'
              }}>
                {agent.personality}
              </div>

              {/* Quote */}
              <div style={{
                background: '#0a0a0a',
                border: `1px solid ${agent.color}33`,
                borderRadius: '4px',
                padding: '12px',
                marginBottom: '16px',
              }}>
                <div style={{ 
                  fontSize: '11px', 
                  color: '#ccc',
                  fontStyle: 'italic',
                  lineHeight: '1.5',
                  textAlign: 'center'
                }}>
                  {agent.quote}
                </div>
              </div>

              {/* Skills */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ 
                  fontSize: '9px', 
                  color: '#666', 
                  letterSpacing: '0.1em',
                  marginBottom: '8px'
                }}>
                  SKILLS
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {agent.skills.map((skill, i) => (
                    <span
                      key={i}
                      className="badge"
                      style={{
                        background: `${agent.color}22`,
                        color: agent.color,
                        fontSize: '9px',
                        padding: '4px 8px',
                      }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Quirks */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ 
                  fontSize: '9px', 
                  color: '#666', 
                  letterSpacing: '0.1em',
                  marginBottom: '8px'
                }}>
                  QUIRKS
                </div>
                <ul style={{ 
                  margin: 0, 
                  paddingLeft: '16px',
                  listStyle: 'none'
                }}>
                  {agent.quirks.map((quirk, i) => (
                    <li 
                      key={i}
                      style={{ 
                        fontSize: '10px', 
                        color: '#888',
                        marginBottom: '4px',
                        position: 'relative'
                      }}
                    >
                      <span style={{ 
                        position: 'absolute', 
                        left: '-12px',
                        color: agent.color 
                      }}>
                        •
                      </span>
                      {quirk}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Fun Fact */}
              <div style={{
                borderTop: '1px solid #1a1a1a',
                paddingTop: '12px',
              }}>
                <div style={{ 
                  fontSize: '9px', 
                  color: '#666', 
                  letterSpacing: '0.1em',
                  marginBottom: '6px'
                }}>
                  FUN FACT
                </div>
                <div style={{ 
                  fontSize: '10px', 
                  color: '#aaa',
                  lineHeight: '1.4'
                }}>
                  {agent.funFact}
                </div>
              </div>

              {/* Agent Status */}
              {agentStatus && (
                <div style={{
                  marginTop: '12px',
                  fontSize: '9px',
                  color: '#666',
                  textAlign: 'center',
                  paddingTop: '12px',
                  borderTop: '1px solid #1a1a1a',
                }}>
                  {agentStatus.summary || 'Standing by...'}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Note */}
      <div className="card" style={{ 
        padding: '24px', 
        marginTop: '32px',
        textAlign: 'center',
        borderColor: '#1a1a1a'
      }}>
        <div style={{ fontSize: '11px', color: '#666', lineHeight: '1.6' }}>
          These AI agents work together to manage your kitchen. Each has their own personality,
          but they all share one goal: making sure you never run out of coffee at 6am.
        </div>
        <div style={{ 
          fontSize: '10px', 
          color: '#444', 
          marginTop: '8px',
          fontStyle: 'italic'
        }}>
          (Except Lebowski. He's just here for the vibes.)
        </div>
      </div>
    </div>
  );
}
