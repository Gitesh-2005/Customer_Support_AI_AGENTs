export interface SupportTicket {
  id: string;
  userId: string;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  createdAt: Date;
  updatedAt: Date;
  attachments?: string[];
  assignedTo?: string;
  resolution?: string;
  aiSuggestions?: AISuggestion[];
}

export interface AISuggestion {
  confidence: number;
  solution: string;
  source: 'knowledge_base' | 'similar_cases' | 'ai_generated';
  timestamp: Date;
}

export interface AIAgent {
  process(input: any): Promise<any>;
  learn(feedback: any): Promise<void>;
}

export interface SummarizationAgent extends AIAgent {
  process(ticket: SupportTicket): Promise<string>;
}

export interface ActionExtractionAgent extends AIAgent {
  process(ticket: SupportTicket): Promise<{
    actions: string[];
    priority: 'low' | 'medium' | 'high' | 'critical';
  }>;
}

export interface TaskRoutingAgent extends AIAgent {
  process(ticket: SupportTicket): Promise<{
    team: string;
    agent: string;
    confidence: number;
  }>;
}

export interface ResolutionRecommendationAgent extends AIAgent {
  process(ticket: SupportTicket): Promise<{
    solutions: AISuggestion[];
    confidence: number;
  }>;
}

export interface ResolutionTimeEstimationAgent extends AIAgent {
  process(ticket: SupportTicket): Promise<{
    estimatedTime: number;
    confidence: number;
    factors: string[];
  }>;
}

export interface ProactivePreventionAgent extends AIAgent {
  process(userId: string): Promise<{
    potentialIssues: string[];
    recommendations: string[];
    confidence: number;
  }>;
} 