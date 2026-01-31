import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import http from 'http';
import { Server as SocketIOServer } from 'socket.io';

const app: Express = express();
app.use(cors());
app.use(bodyParser.json());

// Middleware for error handling
app.use((err: Error, req: Request, res: Response) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

// Middleware for request logging
app.use((req: Request, res: Response, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

const PORT = process.env.PORT || 3000;
const server = http.createServer(app);

const io = new SocketIOServer(server);

io.on('connection', (socket) => {
    console.log('a user connected');
    socket.on('disconnect', () => {
        console.log('user disconnected');
    });
});

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
    res.send({ status: 'ok' });
});

const gracefulShutdown = () => {
    server.close(() => {
        process.exit(0);
    });
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

server.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});