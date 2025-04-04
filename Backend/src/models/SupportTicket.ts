import mongoose, { Schema, Document } from 'mongoose';
import { SupportTicket as ISupportTicket, AISuggestion } from '../types/ai';

export interface ISupportTicketDocument extends ISupportTicket, Document {}

const AISuggestionSchema = new Schema<AISuggestion>({
  confidence: { type: Number, required: true },
  solution: { type: String, required: true },
  source: { 
    type: String, 
    required: true,
    enum: ['knowledge_base', 'similar_cases', 'ai_generated']
  },
  timestamp: { type: Date, default: Date.now }
});

const SupportTicketSchema = new Schema<ISupportTicketDocument>({
  userId: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  status: { 
    type: String, 
    required: true,
    enum: ['open', 'in_progress', 'resolved', 'closed'],
    default: 'open'
  },
  priority: { 
    type: String, 
    required: true,
    enum: ['low', 'medium', 'high', 'critical'],
    default: 'medium'
  },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
  attachments: [{ type: String }],
  assignedTo: { type: String },
  resolution: { type: String },
  aiSuggestions: [AISuggestionSchema]
});

// Update the updatedAt timestamp before saving
SupportTicketSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Create indexes for better query performance
SupportTicketSchema.index({ userId: 1 });
SupportTicketSchema.index({ status: 1 });
SupportTicketSchema.index({ priority: 1 });
SupportTicketSchema.index({ createdAt: -1 });

export const SupportTicket = mongoose.model<ISupportTicketDocument>('SupportTicket', SupportTicketSchema); 