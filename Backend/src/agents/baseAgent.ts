import { AIAgent } from '../types/ai';
import { logger } from '../utils/logger';
import OpenAI from 'openai';

export abstract class BaseAgent implements AIAgent {
  protected openai: OpenAI;
  protected model: string;

  constructor(model: string = 'gpt-4') {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
    this.model = model;
  }

  protected async callOpenAI(prompt: string, maxTokens: number = 1000): Promise<string> {
    try {
      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: maxTokens,
        temperature: 0.7,
      });

      return response.choices[0]?.message?.content || '';
    } catch (error) {
      logger.error('OpenAI API call failed:', error);
      throw error;
    }
  }

  abstract process(input: any): Promise<any>;

  async learn(feedback: any): Promise<void> {
    // Base implementation for learning from feedback
    logger.info('Learning from feedback:', feedback);
  }

  protected calculateConfidence(similarity: number, relevance: number): number {
    // Simple confidence calculation based on similarity and relevance
    return (similarity * 0.7 + relevance * 0.3) * 100;
  }

  protected async extractKeyInformation(text: string): Promise<string[]> {
    const prompt = `Extract key information from the following text. Return only the most important points as a JSON array of strings:\n\n${text}`;
    const response = await this.callOpenAI(prompt);
    try {
      return JSON.parse(response);
    } catch (error) {
      logger.error('Failed to parse key information:', error);
      return [];
    }
  }

  protected async classifyText(text: string, categories: string[]): Promise<string> {
    const prompt = `Classify the following text into one of these categories: ${categories.join(', ')}. Return only the category name:\n\n${text}`;
    return this.callOpenAI(prompt, 50);
  }
} 