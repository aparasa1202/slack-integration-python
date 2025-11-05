const { config } = require('./config');
const { callAgent } = require('./agentClient');
const { callChatGPT } = require('./app/clients/chatgptClient');
const { logInfo, logError } = require('./logger');

function normalizeText(text) {
  return (text || '').trim();
}

function stripBotMention(text, botUserId) {
  if (!text) return '';
  if (!botUserId) return text.trim();
  const mentionPattern = new RegExp(`<@${botUserId}>`, 'gi');
  return text.replace(mentionPattern, '').trim();
}

function extractDirective(text) {
  if (!text) return null;
  if (/@agent\b/i.test(text)) return 'agent';
  if (/@gpt\b/i.test(text)) return 'openai';
  return null;
}

function selectResponder(command) {
  if (command === 'agent') return callAgent;
  if (command === 'openai') return callChatGPT;
  const responders = {
    agent: callAgent,
    openai: callChatGPT
  };
  return responders[config.bot.defaultResponder] || callAgent;
}

function registerListeners(app) {
  app.event('app_mention', async ({ event, say, context }) => {
    await handleMessage({ message: event, say, context });
  });

  app.message(async ({ message, say, context }) => {
    if (message.subtype === 'bot_message' || message.bot_id) return;
    await handleMessage({ message, say, context });
  });
}

async function handleMessage({ message, say, context }) {
  try {
    const text = stripBotMention(normalizeText(message.text), context.botUserId);
    if (!text) return;

    const directive = extractDirective(text);
    const responder = selectResponder(directive);
    const cleanedText = text.replace(/@agent\b/i, '').replace(/@gpt\b/i, '').trim();

    const prompt = cleanedText || text;
    const reply = await responder(prompt);
    const responseText = reply || 'No reply from agent.';

    await say({
      text: responseText,
      thread_ts: message.thread_ts || message.ts
    });

    logInfo('Message processed', {
      channel: message.channel,
      user: message.user,
      directive: directive || config.bot.defaultResponder
    });
  } catch (error) {
    logError('Failed to process message', error);
    await say('Sorry, something went wrong while handling your request.');
  }
}

module.exports = {
  registerListeners
};
