class AiLab < Formula
  desc "AI Lab website, local DeepSeek/Qwen chat, decisions, and watermark tools"
  homepage "https://github.com/iamorlando/homebrew-ai_lab"
  url "https://github.com/iamorlando/homebrew-ai_lab/releases/download/ai_lab-v0.1.14/ai_lab-0.1.14.tar.gz"
  version "0.1.14"
  sha256 "b4e77e4b2949aefae0ae88338b46377eb84475a867aaea5232e72f29b461ecc6"


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
    generate_completions_from_executable(bin/"ai-lab", "completions")
  end

  def caveats
    <<~EOS
      Show AI Lab's managers and screens:
        ai-lab
      Manage downloaded weights, saved models, inference services, and connections:
        ai-lab weights
        ai-lab models
        ai-lab services
        ai-lab apis
      Opening a screen does not download weights or start inference services.
      Existing weights are reused; runtime repairs are reported separately.
      Download missing weights explicitly, then start the selected local API:
        ai-lab weights install qwen --yes
        ai-lab services --action start --model qwen
      Start/restart runs in the foreground; keep that terminal open.
      Create a saved model and open conversational chat by name:
        ai-lab models create --name "My Qwen" --underlying-model qwen
        ai-lab chat --name "My Qwen"
      Add AI Lab's own MCP tools and approval prompts with --self-mcp:
        ai-lab chat --name "My Qwen" --self-mcp
      Chat reports to the current Herdr pane automatically; --herdr-tab opens a tab.
      Tools: Auto/Required switches with Ctrl+T while idle. Required requests a
      native tool call for the user turn and returns to auto after tool results.
      Start a local decision provider separately when using its MCP tools:
        ai-lab weights install laya --yes
        ai-lab services --action start --model laya
      Open Decisions, token completion, or watermark decoding:
        ai-lab decisions
        ai-lab completion
        ai-lab decoder
      Decisions selects a provider with --model laya or its picker.
      Completion opens with a model picker; --name or --model preselects a model.
      Decoder selects a saved generation model with --name or its picker.
      Open the website:
        ai-lab web
      Connect agent clients through MCP, or install the advanced CLI skill:
        ai-lab mcp install --codex
        ai-lab skills install --agent codex --scope user
      Use --claude for MCP, or --agent claude for skills. After upgrading, refresh
      existing client entries/skills with --force and restart the MCP client.
      Read the shipped guide or generate shell completions:
        ai-lab --skill
        ai-lab completions zsh

      Requires Apple Silicon and macOS 15+. No Xcode or Rust installation needed.
      Native setup uses verified prebuilt Metal servers.
      Models, keys, and sessions live in ~/.local/share/ai-lab, outside the Cellar.
      To share an existing website workspace, set AI_LAB_ROOT to that repository.
      Jev needs TYPESAFE_API_KEY or JEV_API_KEY and no local service.
      Native Contrastive uses the CLM checkpoint and Qwen encoder weights:
        ai-lab weights install clm --yes
        ai-lab services --action start --model contrastive
      Inspect connections with apis; shared API schema is completion --api-schema.
    EOS
  end

  test do
    assert_match "AI Lab #{version}", shell_output("#{bin}/ai-lab --version")
    schema = JSON.parse(shell_output("#{bin}/ai-lab completion --api-schema"))
    assert schema.fetch("paths").key?("/api/lab/sessions/{session}/complete")
    assert schema.fetch("paths").fetch("/api/lab/models/{key}").key?("patch")
    discovery = JSON.parse(shell_output("#{bin}/ai-lab --json"))
    public_commands = %w[weights models apis chat decisions completion services decoder skills mcp completions web setup-python-experiments]
    assert_equal public_commands.sort, discovery.fetch("commands").keys.sort
    assert_match "--codex", shell_output("#{bin}/ai-lab mcp install --help")
    chat_help = shell_output("#{bin}/ai-lab chat --help")
    %w[--name --self-mcp --tool-choice --herdr-tab --pane --prompt].each do |flag|
      assert_match flag, chat_help
    end
    completion_help = shell_output("#{bin}/ai-lab completion --help")
    %w[--model --name --prompt --view --layout --session-action --api-schema].each do |flag|
      assert_match flag, completion_help
    end
    assert_match "--name", shell_output("#{bin}/ai-lab models delete --help")
    decisions_help = shell_output("#{bin}/ai-lab decisions --help")
    assert_match "--model", decisions_help
    refute_match "--name", decisions_help
    decoder_help = shell_output("#{bin}/ai-lab decoder --help")
    assert_match "--name", decoder_help
    refute_match "--model", decoder_help
    services_help = shell_output("#{bin}/ai-lab services --help")
    %w[--action --name --model].each do |flag|
      assert_match flag, services_help
    end
    assert_match "--json", shell_output("#{bin}/ai-lab apis --help")
    skills_help = shell_output("#{bin}/ai-lab skills install --help")
    %w[--agent --scope --project --path --force].each do |flag|
      assert_match flag, skills_help
    end
    guide = shell_output("#{bin}/ai-lab --skill")
    assert_equal public_commands.sort, guide.scan(/\bai-lab\s+([a-z][\w-]*)/).flatten.uniq.sort
    assert_match "detect_watermark", guide
    assert_match "--self-mcp", guide
    assert_path_exists bash_completion/"ai-lab"
    assert_path_exists zsh_completion/"_ai-lab"
    assert_path_exists fish_completion/"ai-lab.fish"
    %w[bash zsh fish].each do |shell|
      script = shell_output("#{bin}/ai-lab completions #{shell}")
      public_commands.each { |command| assert_match /\b#{Regexp.escape(command)}\b/, script }
    end
    system libexec/"venv/bin/python", "-c",
           "import jiter, tokenizers, pydantic_core, mcp, jsonschema; " \
           "from ai_lab.agent_backend import AgentBackend; from ai_lab.native_chat import NativeChat; " \
           "import ai_lab.decisions_terminal, ai_lab.decoder_terminal, ai_lab.service_manager, " \
           "ai_lab.api_manager, ai_lab.skills, ai_lab.cli_screens; " \
           "assert jiter.from_json(b'{\"ok\":true}') == {'ok': True}"
  end
end
