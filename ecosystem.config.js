/**
 * PM2 Ecosystem Configuration for Mossland Agentic Orchestrator
 *
 * This configuration manages all services:
 * - Signal collector: Fetches signals every 30 minutes
 * - Debate runner: Runs debates every 6 hours
 * - Web interface: Next.js dashboard
 * - API server: FastAPI backend (optional)
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only moss-signals
 *   pm2 logs moss-ao
 *   pm2 monit
 */

module.exports = {
  apps: [
    // Signal Collector - Runs every 30 minutes
    {
      name: 'moss-signals',
      script: 'python',
      args: '-m agentic_orchestrator.scheduler signal-collect',
      cwd: './src',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      cron_restart: '*/30 * * * *', // Every 30 minutes
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
      },
      env_development: {
        NODE_ENV: 'development',
        PYTHONPATH: './src',
      },
      error_file: './logs/signals-error.log',
      out_file: './logs/signals-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Debate Runner - Runs every 6 hours
    {
      name: 'moss-debate',
      script: 'python',
      args: '-m agentic_orchestrator.scheduler run-debate',
      cwd: './src',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      cron_restart: '0 */6 * * *', // Every 6 hours
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './src',
        OLLAMA_HOST: 'http://localhost:11434',
      },
      env_development: {
        NODE_ENV: 'development',
        PYTHONPATH: './src',
        OLLAMA_HOST: 'http://localhost:11434',
      },
      error_file: './logs/debate-error.log',
      out_file: './logs/debate-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },

    // Backlog Processor - Runs daily at midnight
    {
      name: 'moss-backlog',
      script: 'python',
      args: '-m agentic_orchestrator.scheduler process-backlog',
      cwd: './src',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      cron_restart: '0 0 * * *', // Daily at midnight
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
      name: 'moss-web',
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

    // API Server - FastAPI (Optional)
    {
      name: 'moss-api',
      script: 'uvicorn',
      args: 'agentic_orchestrator.api.main:app --host 0.0.0.0 --port 8000',
      cwd: './src',
      instances: 1,
      autorestart: true,
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
      name: 'moss-health',
      script: 'python',
      args: '-m agentic_orchestrator.scheduler health-check',
      cwd: './src',
      instances: 1,
      autorestart: true,
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
