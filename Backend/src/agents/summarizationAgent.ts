import { BaseAgent } from './baseAgent';
import { SupportTicket, SummarizationAgent as ISummarizationAgent } from '../types/ai';

export class SummarizationAgent extends BaseAgent implements ISummarizationAgent {
  async process(ticket: SupportTicket): Promise<string> {
    const prompt = `Summarize the following support ticket in a clear and concise way. 
    Focus on the main issue, any relevant context, and the current status.
    Format the summary in a way that would be helpful for a support agent to quickly understand the situation.
    
    Ticket Title: ${ticket.title}
    Description: ${ticket.description}
    Status: ${ticket.status}
    Priority: ${ticket.priority}
    ${ticket.attachments ? `Attachments: ${ticket.attachments.join(', ')}` : ''}
    ${ticket.resolution ? `Resolution: ${ticket.resolution}` : ''}`;

    try {
      const summary = await this.callOpenAI(prompt);
      return summary;
    } catch (error) {
      logger.error('Failed to generate summary:', error);
      throw error;
    }
  }

  async learn(feedback: { summary: string; quality: number }): Promise<void> {
    // Store feedback for future model improvement
    logger.info('Learning from summary feedback:', feedback);
    
    // Here you would typically:
    // 1. Store the feedback in a database
    // 2. Use it to fine-tune the summarization model
    // 3. Adjust the prompt template based on feedback
  }

  private async extractKeyPoints(text: string): Promise<string[]> {
    const prompt = `Extract the 3-5 most important points from the following text. 
    Return them as a JSON array of strings:\n\n${text}`;
    
    const response = await this.callOpenAI(prompt);
    try {
      return JSON.parse(response);
    } catch (error) {
      logger.error('Failed to parse key points:', error);
      return [];
    }
  }

  private async identifyTechnicalTerms(text: string): Promise<string[]> {
    const prompt = `Identify any technical terms or jargon in the following text. 
    Return them as a JSON array of strings:\n\n${text}`;
    
    const response = await this.callOpenAI(prompt);
    try {
      return JSON.parse(response);
    } catch (error) {
      logger.error('Failed to parse technical terms:', error);
      return [];
    }
  }
} 