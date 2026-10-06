class AiLab < Formula
  desc "AI Lab website, local DeepSeek/Qwen chat, decisions, and watermark tools"
  homepage "https://github.com/iamorlando/homebrew-ai_lab"
  url "https://github.com/iamorlando/homebrew-ai_lab/releases/download/ai_lab-v0.1.11/ai_lab-0.1.11.tar.gz"
  version "0.1.11"
  sha256 "fcba063d33bb962173f51d86d2098eb7399b5844f5abf69921549f67b8fd21d9"


  depends_on arch: :arm64
  depends_on macos: :sequoia
  depends_on "python@3.13"
  depends_on "uv"

  # PyPI wheels use @rpath IDs and may lack space for longer Cellar paths.
  preserve_rpath

  def install
    ENV["UV_PYTHON_DOWNLOADS"] = "never"
    ENV["UV_CACHE_DIR"] = buildpath/".uv-cache"
    ENV["UV_PROJECT_ENVIRONMENT"] = libexec/"venv"
    # Install the frozen dependency graph into an isolated, non-editable environment.
    system "uv", "sync", "--frozen", "--no-dev", "--no-editable",
           "--python", Formula["python@3.13"].opt_bin/"python3.13"
    bin.install_symlink libexec/"venv/bin/ai-lab"
    generate_completions_from_executable(bin/"ai-lab", "completion")
  end

  def caveats
    <<~EOS
      Start AI Lab for guided setup:
        ai-lab
      The first interactive launch after installation or upgrade offers missing
      DeepSeek (~5.03 GB), Qwen (~5.03 GB), CLM (~16.47 GB), and Laya (~1.69 GB),
      with dependencies.
      Use arrows to move, Space to select models, Enter to download, Esc to skip.
      Progress bars update in place. Existing files are verified and reused.
      Your selection or skip is remembered for this release.
      Inspect or install them explicitly:
        ai-lab downloads list
        ai-lab downloads install qwen --yes
        ai-lab downloads install laya
        ai-lab downloads install clm laya --yes
      Open the existing website:
        ai-lab web
      Open the website without downloading DeepSeek (for hosted Jev or saved data):
        ai-lab web --no-setup
      Or provision from scripts:
        ai-lab setup --yes
      Connect agent tools through uvx (no website or CLI daemon needed):
        ai-lab mcp install --codex
        ai-lab mcp install --claude
      Start local model APIs separately when needed:
        ai-lab models run
        ai-lab models run --qwen
        ai-lab models run --laya
      Create and select a readable Qwen profile:
        ai-lab models create --name Qwen --underlying-model qwen
        ai-lab complete --name Qwen --prompt "Hello"
      Open a local agent with AI Lab's own MCP tools and approval prompts:
        ai-lab agent --name Qwen --self-mcp
      Explicitly request a native tool call for each submitted user turn:
        ai-lab agent --model deepseek --self-mcp --tool-choice required
      Switch Tools: Auto/Required with Ctrl+T while the chat is idle.
      Required still asks for approval and returns to auto after tool results.
      Add --herdr-tab to open it in a new Herdr tab.
      Jev uses its hosted API and needs no local process. After upgrading,
      rerun mcp install with --force to update the client entry.
      Watermark MCP tools accept supplied keys/settings or reuse saved profiles.
      detect_watermark returns native evidence, confidence and a match verdict;
      update_watermarked_model persists overrides across client sessions.
      Restart your MCP client after installation, and restart an older website
      before editing profiles through the updated tools. Read the agent guide:
        ai-lab --skill

      Requires Apple Silicon and macOS 15+. No Xcode or Rust installation needed.
      Setup downloads our verified prebuilt server and ~5 GB of DeepSeek weights.
      Models and sessions live in ~/.local/share/ai-lab, outside Homebrew's Cellar.
      To share an existing website workspace, set AI_LAB_ROOT to that repository.
      Decisions: the CLI automatically syncs TYPESAFE_API_KEY or JEV_API_KEY
      to the website, including on reused launches. No key-related restart needed.
      Laya uses an independent local Node/ONNX server, with automatic Node setup.
      Contrastive setup installs CLM/Qwen3-8B weights and a verified prebuilt
      native Metal server automatically; no Rust or manual binary is needed.
        ai-lab downloads install clm --yes
        ai-lab models run --contrastive
      Discover the API with: ai-lab api schema
    EOS
  end

  test do
    assert_match "AI Lab #{version}", shell_output("#{bin}/ai-lab --version")
    schema = JSON.parse(shell_output("#{bin}/ai-lab api schema"))
    assert schema.fetch("paths").key?("/api/lab/sessions/{session}/complete")
    assert_match "session", shell_output("#{bin}/ai-lab help --json")
    assert_match "--codex", shell_output("#{bin}/ai-lab mcp install --help")
    assert_match "--self-mcp", shell_output("#{bin}/ai-lab agent --help")
    assert_match "--tool-choice", shell_output("#{bin}/ai-lab agent --help")
    assert_match "--herdr-tab", shell_output("#{bin}/ai-lab agent --help")
    assert_match "--pane", shell_output("#{bin}/ai-lab agent-prompt --help")
    assert_match "detect_watermark", shell_output("#{bin}/ai-lab --skill")
    assert schema.fetch("paths").fetch("/api/lab/models/{key}").key?("patch")
    assert_path_exists bash_completion/"ai-lab"
    assert_path_exists zsh_completion/"_ai-lab"
    assert_path_exists fish_completion/"ai-lab.fish"
    system libexec/"venv/bin/python", "-c",
           "import jiter, tokenizers, pydantic_core, mcp, jsonschema; " \
           "from ai_lab.agent_backend import AgentBackend; from ai_lab.native_chat import NativeChat; " \
           "assert jiter.from_json(b'{\"ok\":true}') == {'ok': True}"
  end
end
