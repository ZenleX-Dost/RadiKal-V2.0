/**
 * Quick test script for API connection
 * 
 * Run: node test-api-connection.js
 */

const axios = require('axios');

const API_URL = 'http://localhost:8000';

async function testConnection() {
  console.log('🔗 Testing RadiKal Backend Connection...\n');
  
  try {
    // Test 1: Health check
    console.log('1️⃣  Testing health endpoint...');
    const healthResponse = await axios.get(`${API_URL}/api/xai-qc/health`);
    
    if (healthResponse.status === 200) {
      console.log('   ✅ Backend is alive!');
      console.log(`   📊 Status: ${healthResponse.data.status}`);
      console.log(`   🤖 Model loaded: ${healthResponse.data.model_loaded}`);
      console.log(`   🎮 Device: ${healthResponse.data.device}`);
      console.log(`   📦 Version: ${healthResponse.data.version}`);
    }
    
    console.log('\n✅ All tests passed! Backend is ready.\n');
    console.log('🚀 Next steps:');
    console.log('   1. Run: npm run dev');
    console.log('   2. Open: http://localhost:3000');
    console.log('   3. Upload a weld X-ray image');
    console.log('   4. See YOLOv8 detect defects with 99.88% accuracy!\n');
    
  } catch (error) {
    console.error('\n❌ Connection test failed!\n');
    
    if (error.code === 'ECONNREFUSED') {
      console.error('🔴 Backend server is not running.');
      console.error('\n📝 To start the backend:');
      console.error('   cd backend');
      console.error('   python start_server.py');
      console.error('   OR double-click: backend/START_SERVER.bat\n');
    } else if (error.response) {
      console.error(`🔴 Backend returned error: ${error.response.status}`);
      console.error(`   ${JSON.stringify(error.response.data, null, 2)}`);
    } else {
      console.error(`🔴 Error: ${error.message}`);
    }
    
    process.exit(1);
  }
}

testConnection();
