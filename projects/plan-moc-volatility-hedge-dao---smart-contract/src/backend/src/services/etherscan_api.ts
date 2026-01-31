import axios from 'axios';
import { RateLimiter } from 'limiter';
import * as dotenv from 'dotenv';
import pRetry from 'p-retry';

dotenv.config();

const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY;
if (!ETHERSCAN_API_KEY) {
    throw new Error('ETHEREUM_API_KEY environment variable is not set');
}

const rateLimiter = new RateLimiter({
    tokensPerInterval: 5,
    interval: 'second',
});

class EtherscanService {
    private baseUrl = 'https://api.etherscan.io/api';
    private apiKey = ETHERSCAN_API_KEY;

    async getAccountBalance(address: string): Promise<number> {
        return await this.request('account', { module: 'account', action: 'balance', address, tag: 'latest' });
    }

    async getTransactionCount(address: string): Promise<number> {
        return await this.request('transaction_count', { module: 'account', action: 'txlist', address });
    }

    private async request<T>(cacheKey: string, params: Record<string, any>): Promise<T> {
        const options = {
            method: 'GET',
            url: `${this.baseUrl}?${new URLSearchParams({ ...params, apikey: this.apiKey })}`,
        };

        return pRetry(() => rateLimiter.removeTokens(1).then(() => axios(options)), { retries: 3 }).then(response => {
            if (response.data.status === '0') {
                throw new Error(`Etherscan API error: ${response.data.message}`);
            }
            console.log(`Fetched data for cache key: ${cacheKey}`);
            return response.data.result as T;
        });
    }
}

export default EtherscanService;