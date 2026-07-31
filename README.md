# 🎨 BO2 Emblem Studio

<div align="center">
  <img src="https://raw.githubusercontent.com/BO2-Emblem-Studio/bo2-emblem-studio/main/assets/preview.png" alt="BO2 Emblem Studio Preview" width="800">
  
  **An advanced, open-source desktop application designed for creating, editing, and managing Call of Duty: Black Ops 2 emblems using the power of AI.**
</div>

---

## ✨ Features

- **🎨 Advanced Layer Editor:** Full support for 32 layers with positioning, scaling, rotation, color tweaking, and flipping. Just like the real game, but better.
- **🤖 AI Emblem Generator:** Just type what you want (e.g., *"build a terrifying zombie soldier"*), and watch the AI assemble all 32 layers automatically!
- **⚡ "Continue" System:** Never lose an AI generation again! If the API cuts off the text due to limits, just hit `Continue` and the AI finishes it for you.
- **☁️ Multi-Provider AI Support:** Connects directly with Nvidia API, OpenRouter, Anthropic, OpenAI, or 100% offline via Ollama/LM Studio.
- **💾 Plutonium Integration:** Direct export and injection into your Call of Duty: Black Ops 2 (Plutonium PC) profile.
- **🔄 Undo/Redo System:** Safe editing with full state history and clipboard support.

---

## 🚀 Download & Installation (For Players)

If you just want to use the application without dealing with code:

1. Go to the [Releases](../../releases) tab on the right side of this page.
2. Download `BO2_Emblem_Studio_v1.0.0.zip`.
3. Extract the folder anywhere on your computer.
4. Run `BO2_Emblem_Studio.exe`.

---

## 🧠 Setting up the AI Generator (NVIDIA Free Tier)

NVIDIA offers excellent models for free (like Llama 3.1 70B and Nemotron 3). Here's how to set them up in 2 minutes:

1. Go to [NVIDIA Build](https://build.nvidia.com) and sign in.
2. Search for `meta/llama-3.1-70b-instruct` or `nvidia/nemotron-3-ultra-550b-a55b`.
3. Click on the model, click **Get API Key**, and copy your key (it usually starts with `nvapi-`).
4. Inside BO2 Emblem Studio, click on the **AI Studio** tab.
5. Apply the following settings:
   - **Provider**: `NVIDIA`
   - **Endpoint**: `https://integrate.api.nvidia.com/v1`
   - **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (or whichever you chose)
   - **API Key**: Paste your key here!
6. Click **Test Connection**. If it succeeds, you're ready to go!
7. **Pro-Tip**: If the AI stops generating at 24 layers, it just hit the free text limit. Click the **Continue** button and it will resume right where it stopped!

---

## 🖥️ Using Local AI (100% Offline & Free)

If you have a powerful GPU and prefer to run models locally:

1. Download and install [LM Studio](https://lmstudio.ai/) or [Ollama](https://ollama.com/).
2. Load a good model (like Llama 3 8B or Hermes) and start the local server.
3. In BO2 Emblem Studio, set the **Provider** to `LM Studio` or `Ollama`.
4. Set the **Endpoint** to your local address (e.g., `http://localhost:1234/v1`).
5. You don't need an API Key. Just type your prompt and click **Generate Emblem**!

---

## 🛠️ Development (For Modders & Coders)

Want to add new tools or improve the UI? The code is completely open-source!

To build the project from source, ensure you have **Python 3.11+** installed.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/bo2-emblem-studio.git
cd bo2-emblem-studio

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application directly
python -m bo2_emblem.gui

# 4. Build your own Standalone Executable (.exe)
python scripts/build.py
```
*Note: We included a `.gitignore` so your API keys (stored safely in `~/.bo2_emblem_studio_ai.json`) will never be uploaded accidentally!*

---

## 🤝 Contributing & Community

Pull requests are extremely welcome! If you have ideas to make the AI prompt better, improve the rendering engine, or add features, please open an Issue or a PR. We rely on the community's creativity to make this tool even better.

## 📄 License

This project is open-source and licensed under the MIT License. Feel free to modify, distribute, and enjoy.