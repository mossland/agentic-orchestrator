/**
 * PM2 Ecosystem Configuration for Mossland Agentic Orchestrator
 *
 * This configuration manages all services:
 * - Signal collector: Fetches signals every 10 minutes (TEST) / 30 minutes (PROD)
 * - Trend analyzer: Analyzes trends every 30 minutes (TEST) / 2 hours (PROD)
 * - Debate runner: Runs debates every 1 hour (TEST) / 6 hours (PROD)
 * - Backlog processor: Processes every 30 minutes (TEST) / 4 hours (PROD)
 * - Web interface: Next.js dashboard (port 3000)
 * - API server: FastAPI backend (port 3001)
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only moss-ao-signals
 *   pm2 logs moss-ao-web
 *   pm2 monit
 *
 * TEST MODE SCHEDULE:
 *   Signals:  every 10 minutes
 *   Trends:   every 30 minutes
 *   Debate:   every 1 hour
 *   Backlog:  every 30 minutes
 *
 * PRODUCTION SCHEDULE:
 *   Signals:  every 30 minutes
 *   Trends:   every 2 hours
 *   Debate:   every 6 hours
 *   Backlog:  every 4 hours
 */

// Toggle between TEST and PRODUCTION schedules
const TEST_MODE = false;  // Set to false for production schedules

const SCHEDULES = {
  test: {
    signals: '*/10 * * * *',    // Every 10 minutes
    trends: '*/30 * * * *',     // Every 30 minutes
    debate: '0 * * * *',        // Every hour
    backlog: '*/30 * * * *',    // Every 30 minutes
    health: '*/5 * * * *',      // Every 5 minutes
  },
  production: {
    signals: '*/30 * * * *',    // Every 30 minutes
    trends: '0 */2 * * *',      // Every 2 hours
    debate: '0 */6 * * *',      // Every 6 hours
    backlog: '0 */4 * * *',     // Every 4 hours
    health: '*/5 * * * *',      // Every 5 minutes
  },
};

const schedule = TEST_MODE ? SCHEDULES.test : SCHEDULES.production;

module.exports = {
  apps: [
    // Signal Collector
    // Note: Uses cron_restart for scheduled execution (runs once, waits for next cron trigger)
    {
      name: 'moss-ao-signals',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler signal-collect',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '500M',
      cron_restart: schedule.signals,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/signals-error.log',
      out_file: './logs/signals-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Trend Analyzer
    // Analyzes signals to identify trends using local LLM (Ollama)
    {
      name: 'moss-ao-trends',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler analyze-trends',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '1G',
      cron_restart: schedule.trends,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: 'http://localhost:11434',
      },
      error_file: './logs/trends-error.log',
      out_file: './logs/trends-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Debate Runner
    {
      name: 'moss-ao-debate',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler run-debate',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '2G',
      cron_restart: schedule.debate,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: 'http://localhost:11434',
      },
      error_file: './logs/debate-error.log',
      out_file: './logs/debate-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Backlog Processor
    // Processes idea queue, generates status reports
    {
      name: 'moss-ao-backlog',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler process-backlog',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '1G',
      cron_restart: schedule.backlog,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/backlog-error.log',
      out_file: './logs/backlog-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Web Interface - Next.js Dashboard
    {
      name: 'moss-ao-web',
      script: 'npm',
      args: 'start',
      cwd: './website',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      env_development: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
      error_file: './logs/web-error.log',
      out_file: './logs/web-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // API Server - FastAPI (long-running service)
    {
      name: 'moss-ao-api',
      script: '.venv/bin/python',
      args: '-m uvicorn agentic_orchestrator.api.main:app --host 0.0.0.0 --port 3001',
      cwd: __dirname,
      instances: 1,
      autorestart: true,  // Keep running
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Health Monitor - Checks system health every 5 minutes
    {
      name: 'moss-ao-health',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler health-check',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '200M',
      cron_restart: schedule.health,
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/health-error.log',
      out_file: './logs/health-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },
  ],

  // Deployment configuration
  deploy: {
    production: {
      user: 'deploy',
      host: ['server1.moss.land'],
      ref: 'origin/main',
      repo: 'git@github.com:mossland/agentic-orchestrator.git',
      path: '/var/www/moss-ao',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-setup': '',
      env: {
        NODE_ENV: 'production',
      },
    },
    staging: {
      user: 'deploy',
      host: ['staging.moss.land'],
      ref: 'origin/develop',
      repo: 'git@github.com:mossland/agentic-orchestrator.git',
      path: '/var/www/moss-ao-staging',
      'post-deploy': 'npm install && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env development',
      env: {
        NODE_ENV: 'development',
      },
    },
  },
};
