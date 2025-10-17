'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Loader2 } from 'lucide-react';
import { apiClient, handleApiError } from '@/lib/api';
import { ChatMessage, ChatResponse } from '@/lib/types';
import { getPriorityText, getConfidenceText } from '@/lib/utils';

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatToolResponse = (tool: string, data: Record<string, unknown>): string => {
    if (tool === 'lineup_optimization') {
      const optimal_lineup = data.optimal_lineup as Record<string, {name: string; projection: number; reason: string}> | undefined;
      const projected_total = data.projected_total as number | undefined;
      const confidence_level = data.confidence_level as string | undefined;
      const key_decisions = data.key_decisions as string[] | undefined;
      
      let response = `**Optimal Lineup (Projected: ${projected_total?.toFixed(1) || 'N/A'} pts, Confidence: ${confidence_level || 'Unknown'})**\n\n`;
      
      if (optimal_lineup) {
        Object.entries(optimal_lineup).forEach(([position, playerInfo]) => {
          response += `**${position}:** ${playerInfo.name} (${playerInfo.projection?.toFixed(1)} pts) - ${playerInfo.reason}\n`;
        });
      }
      
      if (key_decisions && key_decisions.length > 0) {
        response += '\n**Key Decisions:**\n';
        key_decisions.forEach((decision: string) => {
          response += `• ${decision}\n`;
        });
      }
      
      return response;
    }
    
    if (tool === 'waiver_wire') {
      const top_recommendations = data.top_recommendations as Array<{
        player_name: string; 
        position: string; 
        nfl_team: string; 
        projected_value: number; 
        priority: 'High' | 'Medium' | 'Low'; 
        reasoning: string;
      }> | undefined;
      
      if (!top_recommendations || top_recommendations.length === 0) {
        return '**No strong waiver wire targets found right now.**';
      }
      
      let response = '**Top Waiver Wire Targets:**\n\n';
      
      top_recommendations.slice(0, 5).forEach((rec) => {
        const priorityText = getPriorityText(rec.priority);
        response += `[${priorityText}] **${rec.player_name}** (${rec.position}) - ${rec.nfl_team}\n`;
        response += `   Projection: ${rec.projected_value?.toFixed(1)} pts\n`;
        response += `   ${rec.reasoning}\n\n`;
      });
      
      return response;
    }
    
    if (tool === 'trade_analysis') {
      const trade_targets = data.trade_targets as Array<{
        target_team: string;
        trade_proposal: {give: string[]; receive: string[]};
        confidence: 'High' | 'Medium' | 'Low';
        trade_reasoning: string;
      }> | undefined;
      
      if (!trade_targets || trade_targets.length === 0) {
        return '**No realistic trade opportunities found at this time.**';
      }
      
      let response = '**Recommended Trade Opportunities:**\n\n';
      
      trade_targets.slice(0, 3).forEach((target, i) => {
        const confidenceText = getConfidenceText(target.confidence);
        response += `**Trade ${i + 1}: ${target.target_team}** [${confidenceText}]\n`;
        if (target.trade_proposal?.give && target.trade_proposal?.receive) {
          response += `**Give:** ${target.trade_proposal.give.join(', ')}\n`;
          response += `**Receive:** ${target.trade_proposal.receive.join(', ')}\n`;
        }
        response += `**Reasoning:** ${target.trade_reasoning}\n\n`;
      });
      
      return response;
    }
    
    if (tool === 'injury_analysis') {
      const summary = data.summary as {healthy_count: number; total_players: number; injury_percentage: number} | undefined;
      const questionable_players = data.questionable_players as Array<{name: string; position: string; nfl_team: string}> | undefined;
      const doubtful_players = data.doubtful_players as Array<{name: string; position: string; nfl_team: string}> | undefined;
      const out_players = data.out_players as Array<{name: string; position: string; nfl_team: string}> | undefined;
      const ir_players = data.ir_players as Array<{name: string; position: string; nfl_team: string}> | undefined;
      
      let response = '**Injury Report Summary:**\n\n';
      if (summary) {
        response += `**Team Health:** ${summary.healthy_count}/${summary.total_players} players healthy (${(100 - summary.injury_percentage).toFixed(0)}%)\n\n`;
      }
      
      if (questionable_players && questionable_players.length > 0) {
        response += '**QUESTIONABLE:**\n';
        questionable_players.forEach((player) => {
          response += `• ${player.name} (${player.position}) - ${player.nfl_team}\n`;
        });
        response += '\n';
      }
      
      if (doubtful_players && doubtful_players.length > 0) {
        response += '**DOUBTFUL:**\n';
        doubtful_players.forEach((player) => {
          response += `• ${player.name} (${player.position}) - ${player.nfl_team}\n`;
        });
        response += '\n';
      }
      
      if (out_players && out_players.length > 0) {
        response += '**OUT:**\n';
        out_players.forEach((player) => {
          response += `• ${player.name} (${player.position}) - ${player.nfl_team}\n`;
        });
        response += '\n';
      }
      
      if (ir_players && ir_players.length > 0) {
        response += '**INJURY RESERVE:**\n';
        ir_players.forEach((player) => {
          response += `• ${player.name} (${player.position}) - ${player.nfl_team}\n`;
        });
        response += '\n';
      }
      
      if ((!questionable_players || questionable_players.length === 0) && 
          (!doubtful_players || doubtful_players.length === 0) && 
          (!out_players || out_players.length === 0) && 
          (!ir_players || ir_players.length === 0)) {
        response += '**Great news! All your players are currently healthy.**\n\n';
      }
      
      return response;
    }
    
    return JSON.stringify(data, null, 2);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await apiClient.sendMessage({
        message: inputMessage,
        conversation_history: messages.map(msg => ({ 
          role: msg.role, 
          content: msg.content || '' 
        })),
        league_context: {
          scoring: '0.5 PPR',
          league_size: 12,
          season: 2025
        }
      });

      // Add tool indicators
      response.tool_calls?.forEach((toolCall) => {
        const toolDisplayNames: Record<string, string> = {
          'optimize_lineup': '🎯 Lineup Optimizer',
          'compare_players': '⚡ Player Comparison',
          'analyze_waiver_wire': '🔍 Waiver Wire Scout',
          'analyze_trade_opportunities': '🤝 Trade Analyzer',
          'analyze_injuries': '🏥 Injury Report'
        };
        
        const displayName = toolDisplayNames[toolCall.tool] || `🔧 ${toolCall.tool}`;
        setMessages(prev => [...prev, { role: 'tool', tool: displayName }]);
      });

      // Add AI response
      if (response.response) {
        setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
      }

      // Process enhanced data from tools
      response.enhanced_data?.forEach((toolData) => {
        if (toolData.error) {
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `❌ Tool Error (${toolData.tool}): ${toolData.error}`
          }]);
        } else if (toolData.data?.status === 'success') {
          const formattedResponse = formatToolResponse(toolData.tool, toolData.data);
          if (formattedResponse) {
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: formattedResponse
            }]);
          }
        }
      });

    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${handleApiError(error)}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const quickQuestions = [
    'Optimize my lineup',
    'Find waiver wire pickups',
    'Check injury reports'
  ];

  const handleQuickQuestion = (question: string) => {
    setInputMessage(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const renderMessage = (message: ChatMessage, index: number) => {
    if (message.role === 'user') {
      return (
        <div key={index} className="flex justify-end mb-4">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-3 rounded-2xl rounded-br-md max-w-xs md:max-w-md">
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        </div>
      );
    }

    if (message.role === 'assistant') {
      return (
        <div key={index} className="flex justify-start mb-4">
          <div className="bg-gray-100 text-black px-4 py-3 rounded-2xl rounded-bl-md max-w-xs md:max-w-md border-l-4 border-indigo-500">
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        </div>
      );
    }

    if (message.role === 'tool') {
      return (
        <div key={index} className="flex justify-center mb-2">
          <div className="bg-gradient-to-r from-pink-500 to-cyan-500 text-white px-4 py-2 rounded-full text-sm font-semibold">
            Using tool: {message.tool}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-black">
          Fantasy AI Assistant
          </h2>
          <button
            onClick={clearChat}
            className="flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Clear
          </button>
        </div>
        <p className="text-sm text-black mt-2">
          Your AI-powered fantasy football expert! I can help with lineup optimization, 
          start/sit decisions, waiver wire analysis, and trade opportunities.
        </p>
      </div>

      {/* Quick Questions */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-sm font-medium text-black mb-3">Quick Questions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {quickQuestions.map((question) => (
            <button
              key={question}
              onClick={() => handleQuickQuestion(question)}
              className="px-3 py-2 text-sm text-black bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded-lg transition-colors text-left"
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="h-96 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="text-center text-black py-8">
            <div className="text-xl mb-2 font-semibold">AI Assistant</div>
            <p>Ask me anything about your fantasy team!</p>
          </div>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 text-black px-4 py-3 rounded-2xl rounded-bl-md">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing your request...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your fantasy team..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-black"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
