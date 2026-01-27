import express, { NextFunction, Request, Response } from 'express';
import * as http from 'http';
import * as https from 'https';
import * as fs from 'fs';
import morgan from 'morgan';
import cors from 'cors';
import bodyParser from 'body-parser';
import { Server } from "socket.io";
import { createServer } from 'http';

const app = express();
app.use(morgan('combined'));
app.use(cors());
app.use(bodyParser.json());

// Graceful shutdown
function gracefulShutdown(signal: string) {
    console.log(`Received ${signal} signal, shutting down gracefully...`);
    server.close(() => {
        console.log('Closed out remaining connections.');
        process.exit(0);
    });
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Environment variables
const PORT = process.env.PORT || 3000;
const ENV = process.env.NODE_ENV || 'development';

app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
    res.send('OK');
});

const httpServer = createServer(app);

// WebSocket Server
const io = new Server(httpServer, {
    cors: {
        origin: '*',
        methods: ["GET", "POST"]
    }
});

io.on('connection', (socket) => {
    console.log('a user connected');
    socket.on('disconnect', () => {
        console.log('user disconnected');
    });
});

// Start the server
httpServer.listen(PORT, () => {
    console.log(`AI-Powered DeFi Portfolio Auto-Rebalancing System running on port ${PORT} in ${ENV} mode`);
});