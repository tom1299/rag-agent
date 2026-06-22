// TODO: Refactor this code

import * as vscode from 'vscode';

import { Message, Role, Task, type SendMessageRequest, type SendMessageResult } from '@a2a-js/sdk';
import { ClientFactory, type Client } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from 'uuid';


export function activate(context: vscode.ExtensionContext) {
	let clientPromise: Promise<Client> | undefined;
	const getClient = () => {
		if (!clientPromise) {
			clientPromise = Promise.resolve().then(() => {
				// TODO: Replace with configurable URL. For the time being use hard coded weather agent
				const factory = new ClientFactory();
				return factory.createFromUrl('http://localhost:9998');
			});
		}
		return clientPromise;
	};

	const outputChannel = vscode.window.createOutputChannel('CodeNanny');
	outputChannel.appendLine('Congratulations, your extension "codenanny" is now active!');

	const participant = vscode.chat.createChatParticipant('codenanny', async (request, _context, response, _token) => {
		const client = await getClient();

		const agentRequest: SendMessageRequest = {
			tenant: '',
			message: {
				messageId: uuidv4(),
				contextId: '',
				taskId: '',
				role: Role.ROLE_USER,
				parts: [
					{
						content: { $case: 'text', value: 'What is the weather in Boston?' },
						metadata: undefined,
						filename: '',
						mediaType: 'text/plain',
					},
				],
				metadata: undefined,
				extensions: [],
				referenceTaskIds: [],
			},
			configuration: undefined,
			metadata: undefined,
		};

		try {
			// Access to open editor and selected text is possible
			// => Pass them to the agent as part of the request
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			const selection = editor.selection;
			const selectedText = editor.document.getText(selection);

			const sendResponse = await client.sendMessage(agentRequest) as SendMessageResult;
			// Check if the response is a Message or a Task and log accordingly
			// TODO: Implement handling of tasks / messages properly
			if ('messageId' in sendResponse) {
				const result = sendResponse as Message;
				const textPart = result.parts.find((part) => part.content?.$case === 'text');
				if (textPart?.content?.$case === 'text') {
					outputChannel.appendLine(`Agent response: ${textPart.content.value}`);
				}
			} else if ('id' in sendResponse) {
				const task = sendResponse as Task;
				response.markdown(task.artifacts[0].parts[0].content?.value || '');
			} else {
				outputChannel.appendLine(`Unknown response type`);
			}

			if ('parts' in sendResponse) {
				const result = sendResponse as Message;
				const textPart = result.parts.find((part) => part.content?.$case === 'text');
				if (textPart?.content?.$case === 'text') {
					outputChannel.appendLine(`Agent response: ${textPart.content.value}`);
				}
			} else {
				outputChannel.appendLine(`Task state: ${sendResponse.status?.state}`);
			}
		} catch (e) {
			outputChannel.appendLine(`Error: ${String(e)}`);
		}

		response.markdown(request.prompt);
	});

	context.subscriptions.push(participant);
}

// This method is called when your extension is deactivated
// TODO: Implement proper cleanup
export function deactivate() {}
