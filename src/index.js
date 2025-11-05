const { App, ExpressReceiver, LogLevel } = require('@slack/bolt');
const { config, validateConfig } = require('./config');
const { registerListeners } = require('./bot');
const { logInfo, logError } = require('./logger');

try {
  validateConfig();
} catch (error) {
  logError('Configuration validation failed', error);
  process.exit(1);
}

const logLevelMap = {
  debug: LogLevel.DEBUG,
  info: LogLevel.INFO,
  warn: LogLevel.WARN,
  error: LogLevel.ERROR
};

const appOptions = {
  token: config.slack.botToken,
  logLevel: logLevelMap[config.logging.level] || LogLevel.INFO
};

let receiver;

if (config.slack.socketMode) {
  Object.assign(appOptions, {
    signingSecret: config.slack.signingSecret,
    socketMode: true,
    appToken: config.slack.appToken
  });
} else {
  receiver = new ExpressReceiver({
    signingSecret: config.slack.signingSecret,
    endpoints: {
      events: config.server.eventsPath
    }
  });
  appOptions.receiver = receiver;
}

const app = new App(appOptions);

registerListeners(app);

app.error(async (error) => {
  logError('Slack app error', error);
});

if (receiver) {
  receiver.router.get('/health', (req, res) => {
    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString()
    });
  });
}

(async () => {
  try {
    if (config.slack.socketMode) {
      await app.start();
      logInfo('Slack bot started in socket mode', {
        environment: config.logging.environment
      });
    } else {
      await app.start({
        port: config.server.port,
        host: config.server.host
      });

      logInfo('Slack bot server started', {
        port: config.server.port,
        host: config.server.host,
        eventsPath: config.server.eventsPath,
        environment: config.logging.environment
      });
    }
  } catch (error) {
    logError('Failed to start Slack bot', error);
    process.exit(1);
  }
})();
