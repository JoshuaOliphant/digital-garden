/**
 * Terminal Emulator for Digital Garden
 * Provides a CLI-like interface for navigating the blog
 */

class Terminal {
  constructor(options = {}) {
    this.inputElement = options.input || document.getElementById('command-input');
    this.outputElement = options.output || document.getElementById('terminal-output');
    this.promptElement = options.prompt || document.getElementById('prompt-path');

    this.history = [];
    this.historyIndex = -1;
    this.currentPath = '/';

    // Command definitions
    this.commands = {
      help: this.cmdHelp.bind(this),
      ls: this.cmdLs.bind(this),
      cd: this.cmdCd.bind(this),
      cat: this.cmdCat.bind(this),
      grep: this.cmdGrep.bind(this),
      clear: this.cmdClear.bind(this),
      pwd: this.cmdPwd.bind(this),
      history: this.cmdHistory.bind(this),
      about: this.cmdAbout.bind(this),
      now: this.cmdNow.bind(this),
      whoami: this.cmdWhoami.bind(this),
      date: this.cmdDate.bind(this),
      tree: this.cmdTree.bind(this),
    };

    // Valid directories
    this.directories = ['/', '/notes', '/til', '/bookmarks', '/how-to', '/tags'];

    this.init();
  }

  init() {
    if (this.inputElement) {
      this.inputElement.addEventListener('keydown', this.handleKeyDown.bind(this));
      this.inputElement.focus();

      // Focus input when clicking anywhere in terminal
      document.querySelector('.terminal')?.addEventListener('click', () => {
        this.inputElement.focus();
      });
    }

    // Handle command links
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('cmd-link')) {
        const cmd = e.target.dataset.cmd;
        if (cmd) {
          this.executeCommand(cmd);
        }
      }
    });
  }

  handleKeyDown(e) {
    switch (e.key) {
      case 'Enter':
        e.preventDefault();
        this.processInput();
        break;
      case 'ArrowUp':
        e.preventDefault();
        this.navigateHistory(-1);
        break;
      case 'ArrowDown':
        e.preventDefault();
        this.navigateHistory(1);
        break;
      case 'Tab':
        e.preventDefault();
        this.autocomplete();
        break;
      case 'c':
        if (e.ctrlKey) {
          e.preventDefault();
          this.cancelInput();
        }
        break;
      case 'l':
        if (e.ctrlKey) {
          e.preventDefault();
          this.cmdClear();
        }
        break;
    }
  }

  processInput() {
    const input = this.inputElement.value.trim();

    if (input) {
      this.history.push(input);
      this.historyIndex = this.history.length;
      this.appendOutput(this.formatPrompt() + input);
      this.executeCommand(input);
    }

    this.inputElement.value = '';
  }

  executeCommand(input) {
    const parts = input.split(/\s+/);
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    if (this.commands[cmd]) {
      this.commands[cmd](args);
    } else if (cmd) {
      // Check if it's a navigation shortcut
      if (this.directories.includes('/' + cmd) || this.directories.includes(cmd)) {
        this.navigate('/' + cmd.replace(/^\//, ''));
      } else {
        this.appendOutput(`<span class="error">command not found: ${cmd}</span>`);
        this.appendOutput(`Type 'help' for available commands.`);
      }
    }
  }

  navigateHistory(direction) {
    const newIndex = this.historyIndex + direction;

    if (newIndex >= 0 && newIndex < this.history.length) {
      this.historyIndex = newIndex;
      this.inputElement.value = this.history[newIndex];
    } else if (newIndex >= this.history.length) {
      this.historyIndex = this.history.length;
      this.inputElement.value = '';
    }
  }

  autocomplete() {
    const input = this.inputElement.value;
    const parts = input.split(/\s+/);

    if (parts.length === 1) {
      // Autocomplete commands
      const matches = Object.keys(this.commands).filter(c => c.startsWith(parts[0]));
      if (matches.length === 1) {
        this.inputElement.value = matches[0] + ' ';
      } else if (matches.length > 1) {
        this.appendOutput(this.formatPrompt() + input);
        this.appendOutput(matches.join('  '));
      }
    } else if (parts.length === 2 && (parts[0] === 'cd' || parts[0] === 'ls')) {
      // Autocomplete directories
      const matches = this.directories.filter(d => d.startsWith(parts[1]) || d.startsWith('/' + parts[1]));
      if (matches.length === 1) {
        this.inputElement.value = parts[0] + ' ' + matches[0];
      } else if (matches.length > 1) {
        this.appendOutput(this.formatPrompt() + input);
        this.appendOutput(matches.join('  '));
      }
    }
  }

  cancelInput() {
    this.appendOutput(this.formatPrompt() + this.inputElement.value + '^C');
    this.inputElement.value = '';
  }

  appendOutput(html) {
    const line = document.createElement('div');
    line.className = 'output-line';
    line.innerHTML = html;
    this.outputElement.appendChild(line);
    this.scrollToBottom();
  }

  scrollToBottom() {
    window.scrollTo(0, document.body.scrollHeight);
  }

  formatPrompt() {
    return `<span class="prompt-user">visitor</span><span class="prompt-at">@</span><span class="prompt-host">garden</span><span class="prompt-separator">:</span><span class="prompt-path">${this.currentPath}</span><span class="prompt-symbol">$</span> `;
  }

  updatePrompt() {
    if (this.promptElement) {
      this.promptElement.textContent = this.currentPath;
    }
  }

  navigate(path) {
    // Use HTMX or regular navigation
    let url;
    switch (path) {
      case '/':
        url = '/';
        break;
      case '/notes':
        url = '/garden';
        break;
      case '/til':
        url = '/til';
        break;
      case '/bookmarks':
        url = '/bookmarks';
        break;
      case '/how-to':
        url = '/garden-paths';
        break;
      case '/tags':
        url = '/topics';
        break;
      default:
        url = path;
    }
    window.location.href = url;
  }

  // Command implementations
  cmdHelp(args) {
    const helpText = `
<div class="help-section">
  <div class="help-title">NAVIGATION</div>
  <div class="help-command"><span class="help-cmd">ls [dir]</span><span class="help-desc">List contents of directory</span></div>
  <div class="help-command"><span class="help-cmd">cd &lt;dir&gt;</span><span class="help-desc">Change to directory</span></div>
  <div class="help-command"><span class="help-cmd">cat &lt;file&gt;</span><span class="help-desc">Read content of a post</span></div>
  <div class="help-command"><span class="help-cmd">tree</span><span class="help-desc">Show directory structure</span></div>
  <div class="help-command"><span class="help-cmd">pwd</span><span class="help-desc">Print current directory</span></div>
</div>
<div class="help-section">
  <div class="help-title">SEARCH</div>
  <div class="help-command"><span class="help-cmd">grep &lt;term&gt;</span><span class="help-desc">Search all content</span></div>
</div>
<div class="help-section">
  <div class="help-title">PAGES</div>
  <div class="help-command"><span class="help-cmd">about</span><span class="help-desc">About the author</span></div>
  <div class="help-command"><span class="help-cmd">now</span><span class="help-desc">What I'm doing now</span></div>
  <div class="help-command"><span class="help-cmd">whoami</span><span class="help-desc">Who is this?</span></div>
</div>
<div class="help-section">
  <div class="help-title">SYSTEM</div>
  <div class="help-command"><span class="help-cmd">clear</span><span class="help-desc">Clear the terminal</span></div>
  <div class="help-command"><span class="help-cmd">history</span><span class="help-desc">Show command history</span></div>
  <div class="help-command"><span class="help-cmd">date</span><span class="help-desc">Show current date</span></div>
  <div class="help-command"><span class="help-cmd">help</span><span class="help-desc">Show this help message</span></div>
</div>
<div class="help-section">
  <div class="help-title">SHORTCUTS</div>
  <div class="help-command"><span class="help-cmd">↑/↓</span><span class="help-desc">Navigate command history</span></div>
  <div class="help-command"><span class="help-cmd">Tab</span><span class="help-desc">Autocomplete</span></div>
  <div class="help-command"><span class="help-cmd">Ctrl+C</span><span class="help-desc">Cancel current input</span></div>
  <div class="help-command"><span class="help-cmd">Ctrl+L</span><span class="help-desc">Clear screen</span></div>
</div>
<div class="help-section">
  <div class="help-title">DIRECTORIES</div>
  <div class="help-command"><span class="help-cmd">/notes</span><span class="help-desc">Long-form articles</span></div>
  <div class="help-command"><span class="help-cmd">/til</span><span class="help-desc">Today I Learned snippets</span></div>
  <div class="help-command"><span class="help-cmd">/bookmarks</span><span class="help-desc">Curated links</span></div>
  <div class="help-command"><span class="help-cmd">/how-to</span><span class="help-desc">Step-by-step guides</span></div>
  <div class="help-command"><span class="help-cmd">/tags</span><span class="help-desc">Browse by topic</span></div>
</div>`;
    this.appendOutput(helpText);
  }

  cmdLs(args) {
    const dir = args[0] || this.currentPath;
    this.appendOutput(`<span class="loading">Loading ${dir}</span>`);

    // Navigate to listing page
    this.navigate(dir);
  }

  cmdCd(args) {
    if (!args[0] || args[0] === '~' || args[0] === '/') {
      this.navigate('/');
      return;
    }

    let targetPath = args[0];
    if (!targetPath.startsWith('/')) {
      targetPath = '/' + targetPath;
    }

    if (this.directories.includes(targetPath)) {
      this.navigate(targetPath);
    } else {
      this.appendOutput(`<span class="error">cd: no such directory: ${args[0]}</span>`);
    }
  }

  cmdCat(args) {
    if (!args[0]) {
      this.appendOutput(`<span class="error">cat: missing file operand</span>`);
      return;
    }

    // Navigate to content page
    const slug = args[0].replace(/\.md$/, '');
    // Try to determine content type from current path or guess
    let url = slug;
    if (!slug.includes('/')) {
      // Guess based on current directory
      const pathMap = {
        '/notes': '/notes/',
        '/til': '/til/',
        '/bookmarks': '/bookmarks/',
        '/how-to': '/how_to/',
      };
      const prefix = pathMap[this.currentPath] || '/notes/';
      url = prefix + slug;
    }
    window.location.href = url;
  }

  cmdGrep(args) {
    if (!args[0]) {
      this.appendOutput(`<span class="error">grep: missing search pattern</span>`);
      return;
    }

    const query = args.join(' ');
    window.location.href = `/topics?search=${encodeURIComponent(query)}`;
  }

  cmdClear() {
    this.outputElement.innerHTML = '';
  }

  cmdPwd() {
    this.appendOutput(this.currentPath);
  }

  cmdHistory() {
    if (this.history.length === 0) {
      this.appendOutput('<span class="help-desc">No commands in history</span>');
      return;
    }

    const historyHtml = this.history
      .map((cmd, i) => `<div class="history-item"><span class="history-number">${i + 1}</span> <span class="cmd">${cmd}</span></div>`)
      .join('');
    this.appendOutput(historyHtml);
  }

  cmdAbout() {
    window.location.href = '/pages/about';
  }

  cmdNow() {
    window.location.href = '/now';
  }

  cmdWhoami() {
    this.appendOutput(`<span class="term-cyan">visitor</span> - exploring Joshua Oliphant's digital garden`);
  }

  cmdDate() {
    const now = new Date();
    this.appendOutput(now.toString());
  }

  cmdTree() {
    const tree = `
<pre>
.
├── <span class="dir-name">notes/</span>          Long-form articles and documentation
├── <span class="dir-name">til/</span>            Today I Learned - quick learnings
├── <span class="dir-name">bookmarks/</span>      Curated external links
├── <span class="dir-name">how-to/</span>         Step-by-step guides
├── <span class="dir-name">tags/</span>           Browse content by topic
├── <span class="file-name">about</span>           About the author
├── <span class="file-name">now</span>             What I'm currently doing
└── <span class="file-name">projects</span>        My projects
</pre>`;
    this.appendOutput(tree);
  }
}

// Initialize terminal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.terminal = new Terminal();
});

// Also initialize if HTMX swaps content
document.addEventListener('htmx:afterSwap', () => {
  if (document.getElementById('command-input')) {
    window.terminal = new Terminal();
  }
});
