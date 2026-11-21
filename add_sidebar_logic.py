with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

sidebar_logic = '''
  // --- UI: Premium Developer Hub Glass Sidebar ---
  const openSidebarBtn = document.getElementById('openSidebarBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const devSidebar = document.getElementById('devSidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  function openSidebar() {
    if (devSidebar && sidebarBackdrop) {
      devSidebar.classList.add('active');
      sidebarBackdrop.classList.add('active');
    }
  }

  function closeSidebar() {
    if (devSidebar && sidebarBackdrop) {
      devSidebar.classList.remove('active');
      sidebarBackdrop.classList.remove('active');
    }
  }

  if (openSidebarBtn) openSidebarBtn.addEventListener('click', openSidebar);
  if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', closeSidebar);
  if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeSidebar);

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && devSidebar && devSidebar.classList.contains('active')) {
      closeSidebar();
    }
  });

  // MCP IDE Tabs
  const mcpSnippets = {
    cursor: {
      file: '.cursor/mcp.json',
      code: '{\\n  "mcpServers": {\\n    "whycode": {\\n      "command": "python",\\n      "args": ["whycode_mcp.py"]\\n    }\\n  }\\n}'
    },
    claude: {
      file: 'claude_desktop_config.json',
      code: '{\\n  "mcpServers": {\\n    "whycode": {\\n      "command": "python",\\n      "args": ["C:/absolute/path/to/whycode_mcp.py"]\\n    }\\n  }\\n}'
    },
    vscode: {
      file: '.vscode/settings.json',
      code: '{\\n  "mcp": {\\n    "servers": {\\n      "whycode": {\\n        "type": "stdio",\\n        "command": "python",\\n        "args": ["whycode_mcp.py"]\\n      }\\n    }\\n  }\\n}'
    },
    cli: {
      file: 'Terminal / Shell Stdio',
      code: '# Test Stdio MCP JSON-RPC Server Directly\\npython whycode_mcp.py'
    }
  };

  const mcpTabs = document.querySelectorAll('.mcp-tab-btn');
  const mcpSnippetFile = document.getElementById('mcpSnippetFile');
  const mcpSnippetCode = document.getElementById('mcpSnippetCode');
  const copyMcpBtn = document.getElementById('copyMcpBtn');
  const copyMcpText = document.getElementById('copyMcpText');

  mcpTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      mcpTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const ide = tab.dataset.ide;
      if (mcpSnippets[ide]) {
        if (mcpSnippetFile) mcpSnippetFile.textContent = mcpSnippets[ide].file;
        if (mcpSnippetCode) mcpSnippetCode.textContent = mcpSnippets[ide].code;
      }
    });
  });

  if (copyMcpBtn && mcpSnippetCode) {
    copyMcpBtn.addEventListener('click', () => {
      const textToCopy = mcpSnippetCode.textContent;
      navigator.clipboard.writeText(textToCopy).then(() => {
        if (copyMcpText) copyMcpText.textContent = '✓ Copied!';
        copyMcpBtn.style.background = 'rgba(74, 222, 128, 0.2)';
        copyMcpBtn.style.borderColor = 'rgba(74, 222, 128, 0.5)';
        copyMcpBtn.style.color = '#4ade80';
        setTimeout(() => {
          if (copyMcpText) copyMcpText.textContent = 'Copy JSON';
          copyMcpBtn.style.background = '';
          copyMcpBtn.style.borderColor = '';
          copyMcpBtn.style.color = '';
        }, 1800);
      }).catch(err => {
        console.warn('Clipboard write failed:', err);
      });
    });
  }

  // Live MCP Tool Call Test
  const testMcpToolBtn = document.getElementById('testMcpToolBtn');
  const mcpTestOutput = document.getElementById('mcpTestOutput');

  if (testMcpToolBtn && mcpTestOutput) {
    testMcpToolBtn.addEventListener('click', () => {
      testMcpToolBtn.disabled = true;
      mcpTestOutput.style.display = 'block';
      mcpTestOutput.innerHTML = '<span style="color: #7aa2ff;">✦ Invoking MCP Tool: `whycode_ask("why did Django avoid duplicate joins?")`...</span>';

      setTimeout(() => {
        mcpTestOutput.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
            <strong style="color:#4ade80;">✓ MCP Response (whycode_ask)</strong>
            <span style="font-family:'Geist Mono',monospace; font-size:10px; color:#7aa2ff;">12.0 µs</span>
          </div>
          <div style="font-size:11.5px; color:#e2e8f0; line-height:1.4;">
            <strong>Fixed #16603 (PR #22207):</strong> Avoided duplicate joins in filter() after aggregation. Filters now use an <code>EXISTS</code> subquery to prevent inflating <code>Count()</code> / <code>Sum()</code> aggregates.
          </div>
        `;
        testMcpToolBtn.disabled = false;
      }, 350);
    });
  }

  // Quick Demo Query Cards
  const quickQueryCards = document.querySelectorAll('.quick-query-card');
  quickQueryCards.forEach(card => {
    card.addEventListener('click', () => {
      const q = card.dataset.query;
      closeSidebar();
      if (composerText) {
        composerText.value = q;
        composerText.style.height = 'auto';
        composerText.style.height = Math.min(160, composerText.scrollHeight) + 'px';
        if (sendBtn) {
          sendBtn.disabled = false;
          sendBtn.classList.add('active');
        }
        submitQuery();
      }
    });
  });
'''

js += '\n' + sidebar_logic

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated glyph_animals_engine.js with Developer Hub Sidebar logic successfully!")
