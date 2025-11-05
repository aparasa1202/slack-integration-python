require('dotenv').config();

const config = {
  server: {
    port: parseInt(process.env.PORT, 10) || 3978,
    host: process.env.HOST || '0.0.0.0',
    eventsPath: process.env.SLACK_EVENTS_PATH || '/slack/events'
  },

  bot: {
    defaultResponder: (process.env.DEFAULT_RESPONDER || 'agent').toLowerCase()
  },

  slack: {
    botToken: process.env.SLACK_BOT_TOKEN,
    signingSecret: process.env.SLACK_SIGNING_SECRET,
    appToken: process.env.SLACK_APP_TOKEN,
    socketMode: String(process.env.SLACK_SOCKET_MODE).toLowerCase() === 'true'
  },

  apis: {
    agent: {
      url: process.env.AGENT_API_URL || 'http://localhost:3001/api/agent',
      timeout: parseInt(process.env.AGENT_API_TIMEOUT, 10) || 30000
    },
    openai: {
      apiKey: process.env.OPENAI_API_KEY,
      apiUrl: process.env.OPENAI_API_URL || 'https://api.openai.com/v1/chat/completions',
      model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
      maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS, 10) || 1000,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE) || 0.7
    }
  },

  logging: {
    level: process.env.LOG_LEVEL || 'info',
    environment: process.env.NODE_ENV || 'development'
  },

  security: {
    jwtSecret: process.env.JWT_SECRET,
    jwtExpiration: process.env.JWT_EXPIRATION || '24h'
  }
};

function validateConfig() {
  const required = ['SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET'];
  const missing = required.filter((key) => !process.env[key]);

  if (missing.length) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  if (config.slack.socketMode && !config.slack.appToken) {
    throw new Error('SLACK_APP_TOKEN is required when SLACK_SOCKET_MODE is true');
  }

  const allowedResponders = ['agent', 'openai'];
  if (!allowedResponders.includes(config.bot.defaultResponder)) {
    throw new Error(`Invalid DEFAULT_RESPONDER value: ${config.bot.defaultResponder}. Expected one of ${allowedResponders.join(', ')}`);
  }
}

module.exports = {
  config,
  validateConfig
};
