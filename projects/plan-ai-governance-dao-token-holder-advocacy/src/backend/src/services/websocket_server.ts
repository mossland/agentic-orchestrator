import WebSocket from 'ws';
import { RateLimiterMemory } from 'rate-limiter-flexible';

const WS_URL = process.env.WS_SERVER_URL || 'wss://example.com/socket';
const MAX_REQUESTS_PER_SECOND = parseInt(process.env.MAX_REQUESTS_PER_SECOND) || 10;

class WebSocketService {
    private ws: WebSocket;
    private rateLimiter: RateLimiterMemory;
    private retryCount: number = 0;
    private maxRetries: number = 5;

    constructor() {
        this.rateLimiter = new RateLimiterMemory({
            points: MAX_REQUESTS_PER_SECOND,
            duration: 1
        });
        this.connect();
    }

    private connect(): void {
        this.ws = new WebSocket(WS_URL);
        this.ws.on('open', () => console.log('Connected to WebSocket server'));
        this.ws.on('message', (data) => console.log(`Received message: ${data}`));
        this.ws.on('error', (err) => this.handleError(err));
        this.ws.on('close', () => {
            if (this.retryCount < this.maxRetries) {
                setTimeout(() => this.connect(), 2000);
                this.retryCount++;
            } else {
                console.error('Max retries reached, could not connect to WebSocket server');
            }
        });
    }

    private handleError(err: Error): void {
        console.error(`WebSocket error occurred: ${err.message}`);
    }

    public sendMessage(message: string): Promise<void> {
        return new Promise((resolve, reject) => {
            this.rateLimiter.consume(1)
                .then(() => {
                    if (this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(message);
                        resolve();
                    } else {
                        reject(new Error('WebSocket is not open'));
                    }
                })
                .catch(reject);
        });
    }

    public close(): void {
        this.ws.close();
    }
}

export default WebSocketService;