const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const { logInfo, logError } = require('./logger');
const { config } = require('./config');

async function callAgent(query) {
  try {
    const res = await fetch(config.apis.agent.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    logInfo('Agent response received', data);
    return data.response || 'Agent did not return any message.';
  } catch (err) {
    logError('Agent API error', err);
    return 'Error connecting to agent.';
  }
}
module.exports = { callAgent };
