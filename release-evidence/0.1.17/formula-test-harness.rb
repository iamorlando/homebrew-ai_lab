require 'json'
require 'open3'
require 'pathname'
class Formula
  class << self
    attr_accessor :test_body
    def desc(*) = nil
    def homepage(*) = nil
    def url(*) = nil
    def version(*) = nil
    def sha256(*) = nil
    def depends_on(*) = nil
    def preserve_rpath(*) = nil
    def test(&block) = self.test_body = block
  end
  def bin = Pathname('/private/tmp/ai-lab-qwen38-release-017/clean-env/bin')
  def libexec = Pathname('/private/tmp/qwen017-formula-harness')
  def version = '0.1.17'
  def shell_output(command, expected=0)
    stdout, stderr, status = Open3.capture3({'PYTHONPATH'=>nil,'PYTHONHOME'=>nil}, command)
    raise "Unexpected exit #{status.exitstatus}, wanted #{expected}: #{command}: #{stderr}" unless status.exitstatus == expected
    stdout
  end
  def assert_match(expected, actual)
    raise "No match for #{expected.inspect}" unless expected.is_a?(Regexp) ? expected.match?(actual) : actual.include?(expected)
  end
  def assert_equal(expected, actual)
    raise "Mismatch #{expected.inspect} != #{actual.inspect}" unless expected == actual
  end
  def system(*arguments)
    raise 'Formula import check failed' unless Kernel.system({'PYTHONPATH'=>nil,'PYTHONHOME'=>nil}, *arguments.map(&:to_s))
  end
end
load '/private/tmp/qwen017-tap/Formula/ai_lab.rb'
AiLab.new.instance_eval(&AiLab.test_body)
puts 'PASS: exact formula test block against installed 0.1.17 wheel (Ruby DSL harness; not actual brew test).'
