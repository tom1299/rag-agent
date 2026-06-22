// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	const outputChannel = vscode.window.createOutputChannel('CodeNanny');
	outputChannel.appendLine('Congratulations, your extension "codenanny" is now active!');

	const participant = vscode.chat.createChatParticipant('codenanny', (request, context, response, token) => {
		response.markdown(request.prompt);
	});

	context.subscriptions.push(participant);
}

// This method is called when your extension is deactivated
export function deactivate() {}
