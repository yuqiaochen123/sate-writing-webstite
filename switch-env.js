#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read the current config
const configPath = path.join(__dirname, 'config.js');
let configContent = fs.readFileSync(configPath, 'utf8');

// Get command line argument
const environment = process.argv[2];

if (!environment || !['local', 'deployed'].includes(environment)) {
    console.log('Usage: node switch-env.js [local|deployed]');
    console.log('Current environment:', configContent.match(/environment:\s*['"]([^'"]+)['"]/)[1]);
    process.exit(1);
}

// Update the environment
configContent = configContent.replace(
    /environment:\s*['"][^'"]+['"]/,
    `environment: '${environment}'`
);

// Write back to file
fs.writeFileSync(configPath, configContent);

console.log(`✅ Switched to ${environment} environment`);
console.log(`Current config: ${configContent.match(/environment:\s*['"]([^'"]+)['"]/)[1]}`);

if (environment === 'deployed') {
    console.log('\n⚠️  Make sure to update the deployed URL in config.js with your actual deployment URL!');
}
