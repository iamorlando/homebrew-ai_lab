class AiLab < Formula
  desc "Local DeepSeek completions and synchronized terminal inspection panes"
  homepage "https://github.com/iamorlando/homebrew-ai_lab"
  url "https://github.com/iamorlando/homebrew-ai_lab/releases/download/ai_lab-v0.1.3/ai_lab-0.1.3.tar.gz"
  version "0.1.3"
  sha256 "b8b115384947d66ca435447f3680a7e17da386417a7b4b3ac029a68e61206eed"


  depends_on arch: :arm64
  depends_on macos: :sequoia
  depends_on "python@3.13"
  depends_on "uv" => :build

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
      Open the existing website:
        ai-lab web
      Or provision from scripts:
        ai-lab setup --yes

      Requires Apple Silicon and macOS 15+. No Xcode or Rust installation needed.
      Setup downloads our verified prebuilt server and ~5 GB of DeepSeek weights.
      Models and sessions live in ~/.local/share/ai-lab, outside Homebrew's Cellar.
      To share an existing website workspace, set AI_LAB_ROOT to that repository.
      Discover the API with: ai-lab api schema
    EOS
  end

  test do
    assert_match "AI Lab #{version}", shell_output("#{bin}/ai-lab --version")
    schema = JSON.parse(shell_output("#{bin}/ai-lab api schema"))
    assert schema.fetch("paths").key?("/api/lab/sessions/{session}/complete")
    assert_match "session", shell_output("#{bin}/ai-lab help --json")
    assert_path_exists bash_completion/"ai-lab"
    assert_path_exists zsh_completion/"_ai-lab"
    assert_path_exists fish_completion/"ai-lab.fish"
    system libexec/"venv/bin/python", "-c",
           "import jiter, tokenizers, pydantic_core; assert jiter.from_json(b'{\"ok\":true}') == {'ok': True}"
  end
end
