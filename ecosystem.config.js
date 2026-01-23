/**
 * PM2 Ecosystem Configuration for Mossland Agentic Orchestrator
 *
 * This configuration manages all services:
 * - Signal collector: Fetches signals every 30 minutes
 * - Debate runner: Runs debates every 6 hours
 * - Web interface: Next.js dashboard (port 3000)
 * - API server: FastAPI backend (port 3001)
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only moss-ao-signals
 *   pm2 logs moss-ao-web
 *   pm2 monit
 */

module.exports = {
  apps: [
    // Signal Collector - Runs every 30 minutes
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
      cron_restart: '*/30 * * * *', // Every 30 minutes
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      error_file: './logs/signals-error.log',
      out_file: './logs/signals-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Trend Analyzer - Runs every 2 hours
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
      cron_restart: '0 */2 * * *', // Every 2 hours
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: 'http://localhost:11434',
      },
      error_file: './logs/trends-error.log',
      out_file: './logs/trends-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Debate Runner - Runs every 6 hours
    {
      name: 'moss-ao-debate',
      script: '.venv/bin/python',
      args: '-m agentic_orchestrator.scheduler run-debate',
      cwd: __dirname,
      instances: 1,
      autorestart: false,  // Don't auto-restart, wait for cron
      watch: false,
      max_memory_restart: '2G',
      cron_restart: '0 */6 * * *', // Every 6 hours
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: 'http://localhost:11434',
      },
      error_file: './logs/debate-error.log',
      out_file: './logs/debate-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Backlog Processor - Runs every 4 hours
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
      cron_restart: '0 */4 * * *', // Every 4 hours
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
      cron_restart: '*/5 * * * *', // Every 5 minutes
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
