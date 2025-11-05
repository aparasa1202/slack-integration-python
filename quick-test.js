const { callChatGPT } = require('./src/app/clients/chatgptClient');

async function quickTest() {
  console.log('🤖 Quick ChatGPT Test\n');
  
  const message = 'Hey, whats the weather like?';
  console.log('👤 You:', message);
  console.log('');
  
  try {
    const response = await callChatGPT(message);
    console.log('🤖 ChatGPT:', response);
  } catch (error) {
    console.log('❌ Error:', error.message);
  }
}

quickTest().catch(console.error);

