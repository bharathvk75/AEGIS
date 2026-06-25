# AEGIS Quick Setup Guide

Follow these steps to get AEGIS fully operational with your integrated camera, AI models, and notifications.

## 1. Connecting Your Camera
1. Open the AEGIS app and go to the **Cameras** tab.
2. Click the **+ Add Integrated Webcam** button at the top right.
3. This will instantly add your computer's built-in webcam.
4. Go to the **Dashboard** tab. You will now see a live preview of your webcam feed! *(Note: We just fixed a bug that was hiding the live preview, so it will now show up correctly).*

## 2. Connecting Your AI Model
Hermes needs a Vision-capable AI model to analyze camera feeds.
1. Go to the **Models** tab.
2. Choose your preferred AI provider:
   - **Ollama**: Requires a local installation of Ollama with a vision model (e.g., `llava`).
   - **LM Studio**: Run a local server in LM Studio with a vision model loaded (e.g., Llama-3-Vision). Enter the server URL (usually `http://localhost:1234/v1`).
   - **Google Gemini**: *Note: Your current Gemini API key is expired. You will need to generate a new key at Google AI Studio and enter it here.*
3. Click **Connect**. Once the status turns green, Hermes is ready to use it!

## 3. Setting Up Notifications (Hermes)
Hermes evaluates events and sends alerts to your phone or app.

**To set up Telegram:**
1. Go to Telegram and message `@BotFather`.
2. Type `/newbot`, give it a name, and copy the **Bot Token** provided.
3. Start a chat with your new bot and send it a message.
4. Get your Chat ID (you can use bots like `@userinfobot` to find your ID).
5. In AEGIS, go to the **Hermes** tab -> **+ Add Channel**.
6. Select **Telegram**, and paste your Token and Chat ID.
7. Click **Save**, then click **Test**. You should receive a test message!

**To set up WhatsApp / SMS (Twilio):**
1. You need a Twilio account. Gather your Account SID, Auth Token, and Twilio phone number.
2. *Crucial Step*: Open your terminal and run `pip install twilio` (this library is required for WhatsApp/SMS to work).
3. In AEGIS, go to the **Hermes** tab -> **+ Add Channel**.
4. Select **WhatsApp** or **SMS**, and enter your Twilio credentials.

## 4. Creating a Trigger
Once your camera and channel are set up:
1. In the **Hermes** tab, scroll down to **Triggers** and click **+ Add Trigger**.
2. Give it a name (e.g., "Intruder Alert").
3. Select your camera.
4. Write a condition (e.g., "Detect if a person is in the frame").
5. Select the notification channel you just created.
6. Check "Capture Snapshot".
7. Save. Hermes will now silently analyze frames every few seconds. When the condition is met, it will instantly notify you via Telegram/WhatsApp with the details!
