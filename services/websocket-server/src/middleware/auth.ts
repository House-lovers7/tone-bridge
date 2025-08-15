import jwt from 'jsonwebtoken';
import axios from 'axios';
import { logger } from '../utils/logger';

interface User {
  id: string;
  email: string;
  tenantId: string;
  role: string;
}

export class AuthMiddleware {
  private jwtSecret: string;
  private apiUrl: string;

  constructor() {
    this.jwtSecret = process.env.JWT_SECRET || 'default-secret';
    this.apiUrl = process.env.API_URL || 'http://localhost:8000';
  }

  async authenticate(token: string): Promise<User | null> {
    if (!token) {
      return null;
    }

    try {
      // First try JWT token
      if (token.startsWith('Bearer ')) {
        token = token.substring(7);
      }

      try {
        const decoded = jwt.verify(token, this.jwtSecret) as any;
        return {
          id: decoded.sub || decoded.id,
          email: decoded.email,
          tenantId: decoded.tenant_id,
          role: decoded.role || 'user'
        };
      } catch (jwtError) {
        // JWT verification failed, try API key
        logger.debug('JWT verification failed, trying API key');
      }

      // Try API key authentication
      const response = await axios.get(`${this.apiUrl}/api/v1/profile`, {
        headers: {
          'X-API-Key': token
        }
      });

      if (response.data) {
        return {
          id: response.data.id,
          email: response.data.email,
          tenantId: response.data.tenant_id,
          role: response.data.role || 'user'
        };
      }

      return null;
    } catch (error) {
      logger.error('Authentication error:', error);
      return null;
    }
  }

  generateToken(user: User): string {
    return jwt.sign(
      {
        sub: user.id,
        email: user.email,
        tenant_id: user.tenantId,
        role: user.role
      },
      this.jwtSecret,
      { expiresIn: '24h' }
    );
  }
}