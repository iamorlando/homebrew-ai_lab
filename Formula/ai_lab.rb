class AiLab < Formula
  desc "AI Lab web app for DeepSeek, CLM decisions, and watermark decoding"
  homepage "https://github.com/iamorlando/homebrew-ai_lab"
  url "https://github.com/iamorlando/homebrew-ai_lab/releases/download/ai_lab-v0.1.15/ai_lab-0.1.15.tar.gz"
  version "0.1.15"
  sha256 "1c07333d2170bdcb3507f971af0679160ff561339a2dbac8ce9830601b66edf4"


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
  end

  def caveats
    <<~EOS
      Open AI Lab:
        ai-lab web
      The website keeps both DeepSeek and CLM APIs running. Keep its terminal open.
      Download missing models explicitly; existing verified weights are reused:
        ai-lab setup install deepseek clm --yes
      Configure saved models in the website's Models page. Completion, Decisions,
      and Watermark decoder are available in the top navigation.
      Connect an agent client to AI Lab's MCP tools:
        ai-lab mcp install --codex
        ai-lab mcp install --claude
      After upgrading, refresh an existing MCP entry with --force and restart the client.
      Jev uses TYPESAFE_API_KEY or JEV_API_KEY; its key stays on the server.

      Models, keys, and sessions live in ~/.local/share/ai-lab, outside the Cellar.
      Keep the same AI_LAB_ROOT if you use a custom workspace. No data cleanup or
      weight redownload is required for this update. Stop an older AI Lab launcher
      before opening the updated website.
      Requires Apple Silicon and macOS 15+. Native setup uses verified prebuilt
      Metal servers; no Rust or Xcode installation is needed.
    EOS
  end

  test do
    assert_match "AI Lab #{version}", shell_output("#{bin}/ai-lab --version")
    discovery = JSON.parse(shell_output("#{bin}/ai-lab --json"))
    assert_equal %w[mcp setup web], discovery.fetch("commands").keys.sort
    assert_match "--port", shell_output("#{bin}/ai-lab web --help")
    assert_match "install", shell_output("#{bin}/ai-lab setup --help")
    assert_match "--codex", shell_output("#{bin}/ai-lab mcp install --help")
    %w[chat completion decisions decoder models services weights apis skills completions].each do |command|
      assert_match "invalid choice", shell_output("#{bin}/ai-lab #{command} --help 2>&1", 2)
    end
    guide = shell_output("#{bin}/ai-lab --skill")
    assert_match "ai-lab web", guide
    assert_match "ai-lab setup", guide
    assert_match "ai-lab mcp", guide
    system libexec/"venv/bin/python", "-c",
           "import jiter, tokenizers, pydantic_core, mcp, jsonschema; " \
           "import ai_lab.web, ai_lab.mcp_server; " \
           "assert jiter.from_json(b'{\"ok\":true}') == {'ok': True}"
  end
end
