import { BaseAgent } from './baseAgent';
import { SupportTicket, SummarizationAgent as ISummarizationAgent } from '../types/ai';
import { logger } from '../utils/logger';

export class SummarizationAgent extends BaseAgent implements ISummarizationAgent {
  private prompt_template = `Analyze the customer support conversation and generate a concise summary in JSON format:
  {
      "summary": "Brief summary of the issue",
      "metadata": {
          "sentiment": "Sentiment analysis result",
          "priority": "Priority level",
          "category": "Issue category (e.g., technical issue, account issue, payment issue)",
          "conversation_id": "Unique conversation ID"
      }
  }
  Focus on identifying the main issue described by the user. Avoid categorizing as a greeting unless explicitly stated.`;

  async process(ticket: SupportTicket): Promise<string> {
    const prompt = `${this.prompt_template}
    
    Ticket Title: ${ticket.title}
    Description: ${ticket.description}
    Status: ${ticket.status}
    Priority: ${ticket.priority}
    ${ticket.attachments ? `Attachments: ${ticket.attachments.join(', ')}` : ''}
    ${ticket.resolution ? `Resolution: ${ticket.resolution}` : ''}`;

    try {
      const summary = await this.callOpenAI(prompt);
      return summary || "No summary available.";
    } catch (error) {
      logger.error('Failed to generate summary:', error);
      return "Error generating summary.";
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