#!/usr/bin/env node

import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

class MyAihelper {
  constructor() {
    this.name = 'MyAihelper';
    this.mission = 'Help automate tasks, answer questions, and guide work.';
  }

  intro() {
    return `Welcome to ${this.name}.\nMission: ${this.mission}\nType your message, or enter \"exit\" to quit.`;
  }

  respond(message) {
    const text = String(message || '').trim();

    if (!text) return 'Please send a message so I can help.';
    if (text.toLowerCase() === 'exit') return 'Goodbye!';

    return `MyAihelper received: "${text}"\nI can help draft ideas, explain code, and guide next steps.`;
  }
}

async function main() {
  const agent = new MyAihelper();
  const rl = readline.createInterface({ input, output });

  console.log(agent.intro());

  while (true) {
    const answer = await rl.question('> ');
    const response = agent.respond(answer);

    if (response === 'Goodbye!') {
      console.log(response);
      break;
    }

    console.log(response);
  }

  rl.close();
}

main().catch((error) => {
  console.error('MyAihelper failed to start:', error);
  process.exitCode = 1;
});
