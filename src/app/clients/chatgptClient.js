const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const { logInfo, logError } = require('../../logger');
const { config } = require('../../config');

async function callChatGPT(query) {
  try {
    const response = await fetch(config.apis.openai.apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apis.openai.apiKey}`
      },
      body: JSON.stringify({
        model: config.apis.openai.model,
        messages: [
          {
            role: 'user',
            content: query
          }
        ],
        max_tokens: config.apis.openai.maxTokens,
        temperature: config.apis.openai.temperature
      })
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    logInfo('ChatGPT response received', { usage: data.usage });
    
    return data.choices[0]?.message?.content || 'No response from ChatGPT.';
  } catch (err) {
    logError('ChatGPT API error', err);
    return 'Error connecting to ChatGPT. Please try again later.';
  }
}

module.exports = { callChatGPT };
