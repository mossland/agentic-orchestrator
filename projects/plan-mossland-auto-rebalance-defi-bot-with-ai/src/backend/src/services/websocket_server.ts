import WebSocket from 'ws';
import { RateLimiterMemory } from 'rate-limiter-flexible';

const WS_URL = process.env.WS_SERVER_URL || 'wss://example.com';
const RATE_LIMIT = parseInt(process.env.RATE_LIMIT || '10');
const RETRY_DELAY_MS = parseInt(process.env.RETRY_DELAY_MS || '5000');

class WebSocketService {
  private ws: WebSocket | null = null;
  private rateLimiter: RateLimiterMemory;

  constructor() {
    this.rateLimiter = new RateLimiterMemory({
      points: RATE_LIMIT,
      duration: 1, // per second
    });
    this.connect();
  }

  private async connect(): Promise<void> {
    try {
      const wsInstance = new WebSocket(WS_URL);
      wsInstance.on('open', () => {
        console.log('Connected to WebSocket server');
      });

      wsInstance.on('message', (data) => {
        console.log(`Received message: ${data}`);
      });

      wsInstance.on('error', (err) => {
        console.error('WebSocket error:', err);
        this.reconnect();
      });

      wsInstance.on('close', () => {
        console.log('Connection closed');
        this.reconnect();
      });

      this.ws = wsInstance;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.reconnect();
    }
  }

  private reconnect(): void {
    setTimeout(() => {
      console.log(`Reconnecting in ${RETRY_DELAY_MS / 1000} seconds...`);
      this.connect();
    }, RETRY_DELAY_MS);
  }

  public async sendMessage(message: string): Promise<void> {
    try {
      const isLimited = await this.rateLimiter.consume(1);
      if (isLimited.consumed) {
        console.log('Message sent:', message);
        this.ws?.send(message);
      } else {
        throw new Error(`Rate limit exceeded. Retry after ${isLimited.msBeforeNext / 1000} seconds.`);
      }
    } catch (error) {
      console.error('Failed to send message:', error.message);
    }
  }

  public close(): void {
    this.ws?.close();
  }
}

export default WebSocketService;