import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

export class AppError extends Error {
  statusCode: number;
  status: string;
  isOperational: boolean;

  constructor(message: string, statusCode: number) {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

export const errorHandler = (
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  if (err instanceof AppError) {
    logger.error('Operational error:', {
      message: err.message,
      statusCode: err.statusCode,
      stack: err.stack
    });

    return res.status(err.statusCode).json({
      status: err.status,
      message: err.message
    });
  }

  // Handle Mongoose validation errors
  if (err.name === 'ValidationError') {
    const errors = Object.values((err as any).errors).map((el: any) => el.message);
    return res.status(400).json({
      status: 'fail',
      message: 'Validation error',
      errors
    });
  }

  // Handle Mongoose duplicate key errors
  if ((err as any).code === 11000) {
    return res.status(400).json({
      status: 'fail',
      message: 'Duplicate field value entered'
    });
  }

  // Handle JWT errors
  if (err.name === 'JsonWebTokenError') {
    return res.status(401).json({
      status: 'fail',
      message: 'Invalid token. Please log in again!'
    });
  }

  if (err.name === 'TokenExpiredError') {
    return res.status(401).json({
      status: 'fail',
      message: 'Your token has expired! Please log in again.'
    });
  }

  // Log unexpected errors
  logger.error('Unexpected error:', {
    message: err.message,
    stack: err.stack,
    name: err.name
  });

  // Send generic error response for unexpected errors
  res.status(500).json({
    status: 'error',
    message: 'Something went wrong!'
  });
}; 