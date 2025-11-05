const { TeamsBot } = require('./src/bot');

// Mock context for simulation
const mockContext = {
  activity: {
    text: '',
    from: { id: 'terminal-user' },
    recipient: { id: 'bot' },
    conversation: { id: 'terminal-conv' }
  },
  sendActivity: async (message) => {
    console.log('🤖 Bot:', message);
    return { id: 'simulation-response' };
  }
};

async function simulateBot() {
  console.log('🤖 Bot Simulation (without API calls)\n');
  
  const bot = new TeamsBot();
  
  // Test your message
  const message = '!gpt Hey, whats the weather like?';
  console.log('👤 You:', message);
  console.log('');
  
  mockContext.activity.text = message;
  
  try {
    await bot.onMessage(mockContext, async () => {});
  } catch (error) {
    console.log('❌ Error:', error.message);
  }
  
  console.log('\n💡 This shows how your bot would process the message.');
  console.log('   (The actual ChatGPT response is blocked by rate limits)');
}

simulateBot().catch(console.error);

