/**
 * Terminal Emulator for An Oliphant Never Forgets
 * Provides a CLI-like interface for navigating the blog
 */

class Terminal {
  constructor(options = {}) {
    this.inputElement = options.input || document.getElementById('command-input');
    this.outputElement = options.output || document.getElementById('terminal-output');
    this.promptElement = options.prompt || document.getElementById('prompt-path');

    this.history = [];
    this.historyIndex = -1;
    this.currentPath = this.getPathFromUrl();

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
      now: this.cmdNow.bind(this),
      whoami: this.cmdWhoami.bind(this),
      date: this.cmdDate.bind(this),
      tree: this.cmdTree.bind(this),
    };

    // Cache for content items (for autocomplete)
    this.contentCache = {};

    // Valid directories
    this.directories = ['/', '/notes', '/til', '/bookmarks', '/how-to', '/tags'];

    // Autocomplete selection state
    this.autocompleteState = null;

    this.init();
  }

  init() {
    if (this.inputElement) {
      this.inputElement.addEventListener('keydown', this.handleKeyDown.bind(this));
      this.inputElement.focus();

      // Focus input when clicking anywhere in terminal
      document.querySelector('.terminal')?.addEventListener('click', (e) => {
        // Don't steal focus if clicking on an autocomplete item
        if (!e.target.closest('.autocomplete-menu')) {
          this.inputElement.focus();
        }
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
      // Handle autocomplete item clicks
      if (e.target.closest('.autocomplete-item')) {
        const item = e.target.closest('.autocomplete-item');
        const slug = item.dataset.slug;
        if (slug) {
          this.selectAutocompleteItem(slug);
        }
      }
    });
  }

  handleKeyDown(e) {
    // If autocomplete menu is open, handle navigation
    if (this.autocompleteState) {
      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          this.navigateAutocomplete(-1);
          return;
        case 'ArrowDown':
          e.preventDefault();
          this.navigateAutocomplete(1);
          return;
        case 'Enter':
          e.preventDefault();
          this.confirmAutocompleteSelection();
          return;
        case 'Escape':
          e.preventDefault();
          this.closeAutocomplete();
          return;
        case 'Tab':
          e.preventDefault();
          this.navigateAutocomplete(1);
          return;
      }
    }

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

  async executeCommand(input) {
    const parts = input.split(/\s+/);
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    if (this.commands[cmd]) {
      // Handle both sync and async commands
      await this.commands[cmd](args);
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

  async autocomplete() {
    const input = this.inputElement.value;
    const parts = input.split(/\s+/);

    if (parts.length === 1) {
      // Autocomplete commands
      const matches = Object.keys(this.commands).filter(c => c.startsWith(parts[0]));
      if (matches.length === 1) {
        this.inputElement.value = matches[0] + ' ';
      } else if (matches.length > 1) {
        this.showAutocompleteMenu(matches.map(m => ({ slug: m, title: '', type: 'command' })), 'command');
      }
    } else if (parts.length === 2 && (parts[0] === 'cd' || parts[0] === 'ls')) {
      // Autocomplete directories
      const matches = this.directories.filter(d => d.startsWith(parts[1]) || d.startsWith('/' + parts[1]));
      if (matches.length === 1) {
        this.inputElement.value = parts[0] + ' ' + matches[0];
      } else if (matches.length > 1) {
        this.showAutocompleteMenu(matches.map(m => ({ slug: m, title: '', type: 'directory' })), 'directory');
      }
    } else if (parts.length === 2 && parts[0] === 'cat') {
      // Autocomplete content slugs
      await this.autocompleteContent(parts[1]);
    }
  }

  async autocompleteContent(partial) {
    // Fetch content slugs if not cached
    if (Object.keys(this.contentCache).length === 0) {
      try {
        const response = await fetch('/api/content-slugs');
        this.contentCache = await response.json();
      } catch (e) {
        this.appendOutput(`<span class="error">Failed to fetch content list</span>`);
        return;
      }
    }

    // Determine which content type to search based on current path
    const pathToType = {
      '/notes': 'notes',
      '/til': 'til',
      '/bookmarks': 'bookmarks',
      '/how-to': 'how_to',
    };
    const contentType = pathToType[this.currentPath];

    // Collect all matching slugs
    let allSlugs = [];
    const typesToSearch = contentType ? [contentType] : Object.keys(this.contentCache);

    for (const type of typesToSearch) {
      const items = this.contentCache[type] || [];
      for (const item of items) {
        if (item.slug.toLowerCase().startsWith(partial.toLowerCase()) ||
            item.title.toLowerCase().includes(partial.toLowerCase())) {
          allSlugs.push({
            slug: item.slug,
            title: item.title,
            type: type,
          });
        }
      }
    }

    if (allSlugs.length === 1) {
      this.inputElement.value = 'cat ' + allSlugs[0].slug;
    } else if (allSlugs.length > 0) {
      this.showAutocompleteMenu(allSlugs.slice(0, 15), 'content');
    } else {
      this.appendOutput(this.formatPrompt() + 'cat ' + partial);
      this.appendOutput(`<span class="help-desc">No matching content found</span>`);
    }
  }

  showAutocompleteMenu(items, type) {
    // Close any existing menu
    this.closeAutocomplete();

    // Create menu container
    const menu = document.createElement('div');
    menu.className = 'autocomplete-menu';
    menu.id = 'autocomplete-menu';

    // Add header
    const header = document.createElement('div');
    header.className = 'autocomplete-header';
    header.innerHTML = `<span class="autocomplete-hint">↑↓ navigate • Enter select • Esc close</span>`;
    menu.appendChild(header);

    // Add items
    items.forEach((item, index) => {
      const itemEl = document.createElement('div');
      itemEl.className = 'autocomplete-item' + (index === 0 ? ' selected' : '');
      itemEl.dataset.slug = item.slug;
      itemEl.dataset.index = index;

      if (type === 'content') {
        itemEl.innerHTML = `
          <span class="autocomplete-slug">${item.slug}</span>
          <span class="autocomplete-title">${item.title}</span>
          <span class="autocomplete-type">[${item.type}]</span>
        `;
      } else {
        itemEl.innerHTML = `<span class="autocomplete-slug">${item.slug}</span>`;
      }

      menu.appendChild(itemEl);
    });

    // Position menu near input
    const inputWrapper = document.querySelector('.command-input-wrapper');
    inputWrapper.insertAdjacentElement('beforebegin', menu);

    // Store state
    this.autocompleteState = {
      items: items,
      selectedIndex: 0,
      type: type,
      menuElement: menu,
    };

    this.scrollToBottom();
  }

  navigateAutocomplete(direction) {
    if (!this.autocompleteState) return;

    const { items, selectedIndex, menuElement } = this.autocompleteState;
    const newIndex = Math.max(0, Math.min(items.length - 1, selectedIndex + direction));

    // Update selection
    const allItems = menuElement.querySelectorAll('.autocomplete-item');
    allItems[selectedIndex].classList.remove('selected');
    allItems[newIndex].classList.add('selected');

    // Scroll item into view
    allItems[newIndex].scrollIntoView({ block: 'nearest' });

    this.autocompleteState.selectedIndex = newIndex;
  }

  confirmAutocompleteSelection() {
    if (!this.autocompleteState) return;

    const { items, selectedIndex, type } = this.autocompleteState;
    const selectedItem = items[selectedIndex];

    this.selectAutocompleteItem(selectedItem.slug, type);
  }

  selectAutocompleteItem(slug, type) {
    const currentType = this.autocompleteState?.type || type;

    if (currentType === 'command') {
      this.inputElement.value = slug + ' ';
      this.closeAutocomplete();
      this.inputElement.focus();
    } else if (currentType === 'directory') {
      const parts = this.inputElement.value.split(/\s+/);
      this.inputElement.value = parts[0] + ' ' + slug;
      this.closeAutocomplete();
      this.inputElement.focus();
    } else {
      // For content, navigate directly to the page
      const selectedItem = this.autocompleteState?.items.find(i => i.slug === slug);
      const contentType = selectedItem?.type || 'notes';
      this.closeAutocomplete();
      this.navigateToContent(slug, contentType);
    }
  }

  navigateToContent(slug, contentType) {
    // Map content types to URL paths
    const typeToPath = {
      'notes': '/notes/',
      'til': '/til/',
      'bookmarks': '/bookmarks/',
      'how_to': '/how_to/',
    };
    const basePath = typeToPath[contentType] || '/notes/';
    window.location.href = basePath + slug;
  }

  closeAutocomplete() {
    if (this.autocompleteState?.menuElement) {
      this.autocompleteState.menuElement.remove();
    }
    this.autocompleteState = null;
  }

  cancelInput() {
    this.closeAutocomplete();
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

  getPathFromUrl() {
    const pathname = window.location.pathname;

    // Map URL paths to terminal paths
    const urlToPath = {
      '/': '/',
      '/garden': '/notes',
      '/til': '/til',
      '/bookmarks': '/bookmarks',
      '/how_to': '/how-to',
      '/topics': '/tags',
      '/tags': '/tags',
      '/now': '/now',
    };

    // Check for exact match first
    if (urlToPath[pathname]) {
      return urlToPath[pathname];
    }

    // Check for content paths (e.g., /notes/some-article)
    if (pathname.startsWith('/notes/')) return '/notes';
    if (pathname.startsWith('/til/')) return '/til';
    if (pathname.startsWith('/bookmarks/')) return '/bookmarks';
    if (pathname.startsWith('/how_to/')) return '/how-to';
    if (pathname.startsWith('/tags/')) return '/tags';

    // Default to root
    return '/';
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

  async cmdGrep(args) {
    if (!args[0]) {
      this.appendOutput(`<span class="error">grep: missing search pattern</span>`);
      return;
    }

    const query = args.join(' ');
    this.appendOutput(`<span style="color: var(--term-gray);">Searching for "${query}"...</span>`);

    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();

      if (data.results.length === 0) {
        this.appendOutput(`<span style="color: var(--term-amber);">No results found for "${query}"</span>`);
        return;
      }

      // Display results header
      this.appendOutput(`<span style="color: var(--term-green);">Found ${data.total} result${data.total !== 1 ? 's' : ''} for "${query}":</span>`);
      this.appendOutput('');

      // Display each result
      for (const result of data.results) {
        const typeColor = {
          'notes': 'var(--term-cyan)',
          'til': 'var(--term-yellow)',
          'bookmarks': 'var(--term-magenta)',
          'how_to': 'var(--term-amber)',
        }[result.content_type] || 'var(--term-gray)';

        const url = `/${result.content_type}/${result.slug}`;
        this.appendOutput(`<span style="color: ${typeColor};">[${result.content_type}]</span> <a href="${url}">${result.title}</a>`);

        // Show excerpt if available
        if (result.excerpt) {
          const cleanExcerpt = result.excerpt
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .substring(0, 150);
          this.appendOutput(`<span style="color: var(--term-gray); font-size: 0.9em; margin-left: 1rem;">  ${cleanExcerpt}</span>`);
        }
      }

      if (data.total > data.results.length) {
        this.appendOutput('');
        this.appendOutput(`<span style="color: var(--term-gray);">Showing ${data.results.length} of ${data.total} results</span>`);
      }

    } catch (error) {
      this.appendOutput(`<span class="error">grep: search failed - ${error.message}</span>`);
    }
  }

  cmdClear() {
    this.closeAutocomplete();
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

  cmdNow() {
    window.location.href = '/now';
  }

  cmdWhoami() {
    this.appendOutput(`<span class="term-cyan">visitor</span> - exploring Joshua Oliphant's blog (An Oliphant Never Forgets)`);
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
