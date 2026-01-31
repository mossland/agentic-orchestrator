import WebSocket from 'ws';
import { RateLimiterMemory } from 'rate-limiter-flexible';

const WS_URL = process.env.WS_SERVER_URL || 'wss://example.com/socket';
const RATE_LIMIT = parseInt(process.env.RATE_LIMIT || '10');
const RETRY_DELAY_MS = parseInt(process.env.RETRY_DELAY_MS || '5000');

class WebSocketService {
  private ws: WebSocket | null;
  private rateLimiter: RateLimiterMemory;

  constructor() {
    this.ws = null;
    this.rateLimiter = new RateLimiterMemory({
      points: RATE_LIMIT,
      duration: 1, // per second
    });
  }

  public connect(): void {
    this.ws = new WebSocket(WS_URL);

    this.ws.on('open', () => {
      console.log('Connected to WebSocket server');
    });

    this.ws.on('message', (data) => {
      console.log(`Received message: ${data}`);
    });

    this.ws.on('error', (err) => {
      console.error('WebSocket error:', err);
    });

    this.ws.on('close', () => {
      console.log('Disconnected from WebSocket server');
      setTimeout(() => this.connect(), RETRY_DELAY_MS);
    });
  }

  public async sendMessage(message: string): Promise<void> {
    try {
      await this.rateLimiter.consume();
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ message }));
      } else {
        console.error('WebSocket is not open, cannot send message');
      }
    } catch (err: any) {
      if (err instanceof RateLimiterMemory.RateLimiterError) {
        console.warn(`Rate limit exceeded. Retry after ${err.msBeforeNext / 1000} seconds.`);
      } else {
        console.error('Failed to send message:', err);
      }
    }
  }

  public disconnect(): void {
    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.close();
    }
  }
}

export default WebSocketService;