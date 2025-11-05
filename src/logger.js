const logLevel = process.env.LOG_LEVEL || 'info';
const isDevelopment = process.env.NODE_ENV === 'development';

// Log levels hierarchy
const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3
};

function shouldLog(level) {
  return LOG_LEVELS[level] <= LOG_LEVELS[logLevel];
}

function formatLog(level, message, data = null) {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    level: level.toUpperCase(),
    message
  };
  
  if (data) {
    logEntry.data = data;
  }
  
  return isDevelopment ? 
    `${timestamp} [${level.toUpperCase()}] ${message}${data ? ' | ' + JSON.stringify(data) : ''}` :
    JSON.stringify(logEntry);
}

function logInfo(message, data = null) {
  if (shouldLog('info')) {
    console.log(formatLog('info', message, data));
  }
}

function logError(message, error = null) {
  if (shouldLog('error')) {
    const errorData = error ? {
      message: error.message,
      stack: error.stack,
      ...(error.response && { response: error.response })
    } : null;
    console.error(formatLog('error', message, errorData));
  }
}

function logWarn(message, data = null) {
  if (shouldLog('warn')) {
    console.warn(formatLog('warn', message, data));
  }
}

function logDebug(message, data = null) {
  if (shouldLog('debug')) {
    console.log(formatLog('debug', message, data));
  }
}

module.exports = {
  logInfo,
  logError,
  logWarn,
  logDebug
};
