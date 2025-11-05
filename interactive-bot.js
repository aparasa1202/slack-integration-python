const { TeamsBot } = require('./src/bot');
const { callAgent } = require('./src/agentClient');
const { callChatGPT } = require('./src/app/clients/chatgptClient');
const readline = require('readline');

// Mock context for terminal interaction
const mockContext = {
  activity: {
    text: '',
    from: { id: 'terminal-user' },
    recipient: { id: 'bot' },
    conversation: { id: 'terminal-conv' }
  },
  sendActivity: async (message) => {
    console.log('🤖 Bot:', message);
    return { id: 'terminal-response' };
  }
};

async function interactiveBot() {
  console.log('🤖 Interactive Teams Bot - Terminal Mode\n');
  
  // Check environment
  if (!process.env.OPENAI_API_KEY) {
    console.log('❌ OPENAI_API_KEY not found');
    console.log('Please set your API key:');
    console.log('export OPENAI_API_KEY="your-key-here"');
    return;
  }
  
  console.log('✅ OpenAI API connected');
  console.log('💡 Commands:');
  console.log('  !gpt <message>  - Chat with ChatGPT');
  console.log('  !agent <message> - Chat with your agent');
  console.log('  <message>       - Default to agent');
  console.log('  /quit           - Exit\n');
  
  // Create bot instance
  const bot = new TeamsBot();
  
  // Create readline interface
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  const askQuestion = () => {
    rl.question('👤 You: ', async (input) => {
      if (input.toLowerCase() === '/quit') {
        console.log('👋 Goodbye!');
        rl.close();
        return;
      }
      
      if (input.trim() === '') {
        askQuestion();
        return;
      }
      
      // Process message through bot
      mockContext.activity.text = input.trim();
      
      try {
        await bot.onMessage(mockContext, async () => {});
      } catch (error) {
        console.log('❌ Error:', error.message);
      }
      
      console.log(''); // Add spacing
      askQuestion();
    });
  };
  
  askQuestion();
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Goodbye!');
  process.exit(0);
});

interactiveBot().catch(console.error);

