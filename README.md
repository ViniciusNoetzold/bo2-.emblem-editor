# BO2 Emblem Studio

**BO2 Emblem Studio** is an advanced desktop application designed for creating, editing, and managing Call of Duty: Black Ops 2 emblems. Built with a powerful AI integration, you can instantly generate complex emblems using text prompts via Nvidia NIM, OpenRouter, or your local LLM (Hermes/Ollama/LM Studio).

![BO2 Emblem Studio](https://raw.githubusercontent.com/BO2-Emblem-Studio/bo2-emblem-studio/main/assets/preview.png)

## 🌟 Features

- **🎨 Advanced Layer Editor:** Full support for 32 layers with positioning, scaling, rotation, color tweaking, and flipping.
- **🤖 AI Emblem Generator:** Just type what you want (e.g., "build an alien drinking soda") and watch the AI assemble the 32 layers automatically.
- **☁️ Multi-Provider AI Support:** Connects directly with Nvidia API, OpenRouter, Anthropic, OpenAI, or 100% offline via Ollama/LM Studio.
- **💾 Plutonium Integration:** Direct export and injection into your Call of Duty: Black Ops 2 (Plutonium PC) profile.
- **🔄 Undo/Redo System:** Safe editing with full state history and clipboard support.

## 🚀 Download & Installation

1. Go to the [Releases](../../releases) tab.
2. Download `BO2_Emblem_Studio_v1.0.zip`.
3. Extract the folder anywhere on your computer.
4. Run `BO2_Emblem_Studio.exe`.

## 🧠 Using the AI Generator (Nvidia NIM)

If you want to use the high-quality AI models from Nvidia for free:
1. Go to [Nvidia Build](https://build.nvidia.com) and get your free API Key (starts with `nvapi-`).
2. Inside BO2 Emblem Studio, click on the **AI Studio** tab.
3. Select **Provider**: `NVIDIA`.
4. Set **Endpoint**: `https://integrate.api.nvidia.com/v1`.
5. Set **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (or `meta/llama-3.1-70b-instruct`).
6. Paste your **API Key**.
7. Click **Test Connection** to verify, type your prompt, and click **Generate Emblem**!

## 🖥️ Using Local AI (100% Offline & Free)

If you have a good GPU and prefer to run models locally:
1. Download and install [LM Studio](https://lmstudio.ai/) or [Ollama](https://ollama.com/).
2. Load a model and start the local server.
3. In BO2 Emblem Studio, set the **Provider** to `LM Studio` or `Ollama`.
4. Set the **Endpoint** to your local address (e.g., `http://localhost:1234/v1`).
5. You don't need an API Key. Click **Generate Emblem**!

## 🛠️ Development & Building from Source

To build the project from source, ensure you have Python 3.11+ installed.

```bash
# Clone the repository
git clone https://github.com/your-username/bo2-emblem-studio.git
cd bo2-emblem-studio

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m bo2_emblem.gui

# Build the standalone executable
python scripts/build.py
```

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
This project is licensed under the MIT License.