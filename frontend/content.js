(function() {
    // Prevent multiple injections on the same page
    if (document.getElementById('web-chatbot-container')) return;

    // Load Google Font
    const fontLink = document.createElement('link');
    fontLink.rel = 'stylesheet';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
    document.head.appendChild(fontLink);

    // Create container for the widget
    const container = document.createElement('div');
    container.id = 'web-chatbot-container';
    // Load theme preference: respect manual override if set, otherwise follow system theme
    const savedTheme = localStorage.getItem('web-chatbot-theme');
    const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialIsDark = savedTheme ? savedTheme === 'dark' : systemPrefersDark;
    if (initialIsDark) container.classList.add('dark-mode');
    document.body.appendChild(container);

    // Inject HTML Structure
    container.innerHTML = `
        <div id="web-chatbot-trigger" title="Chat with Aletheia">
            <svg id="cb-trigger-icon" viewBox="0 0 32 32" width="30" height="30" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="16" cy="16" r="15" fill="none" stroke="currentColor" stroke-width="1.3" opacity="0.35"></circle>
                <path d="M16 6.5 L23.5 24.5 L19.7 24.5 L17.85 19.8 L14.15 19.8 L12.3 24.5 L8.5 24.5 Z M16 11.3 L14.85 16.4 L17.15 16.4 Z" fill="currentColor"></path>
                <circle cx="16" cy="16" r="3.1" fill="none" stroke="currentColor" stroke-width="1.4" opacity="0.9"></circle>
            </svg>
            <span id="cb-trigger-label" aria-hidden="true">
                <span>Ask</span>
                <span>to</span>
                <span>chatbot</span>
            </span>
        </div>
        <div id="web-chatbot-window" class="hidden">
            <!-- Header -->
            <div id="web-chatbot-header">
                <div class="cb-header-avatar">
                    <svg viewBox="0 0 100 100" width="24" height="24" xmlns="http://www.w3.org/2000/svg">
                      <defs>
                        <linearGradient id="a_grad" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stop-color="#00aaff" />
                          <stop offset="100%" stop-color="#000088" />
                        </linearGradient>
                      </defs>
                      <path d="M50 15 L15 85 L85 85 Z" fill="none" stroke="url(#a_grad)" stroke-width="4" stroke-linejoin="round"/>
                      <path d="M35 60 L65 60" fill="none" stroke="url(#a_grad)" stroke-width="4" stroke-linecap="round"/>
                      <path d="M15 85 L50 85 M50 15 L50 85" fill="none" stroke="url(#a_grad)" stroke-width="2" opacity="0.5"/>
                      <circle cx="50" cy="15" r="5" fill="#00aaff"/>
                      <circle cx="15" cy="85" r="5" fill="#000088"/>
                      <circle cx="85" cy="85" r="5" fill="#000088"/>
                      <circle cx="35" cy="60" r="5" fill="#0066cc"/>
                      <circle cx="65" cy="60" r="5" fill="#0066cc"/>
                      <circle cx="50" cy="85" r="5" fill="#000088"/>
                      <circle cx="32.5" cy="42.5" r="5" fill="#0088dd"/>
                      <circle cx="67.5" cy="42.5" r="5" fill="#0088dd"/>
                      <polygon points="50,40 52.5,47 60,47 54,51.5 56.5,58.5 50,54 43.5,58.5 46,51.5 40,47 47.5,47" fill="url(#a_grad)"/>
                    </svg>
                </div>
                <div class="cb-header-info">
                    <div class="cb-header-title">CHATBOT ALETHEIA</div>
                    <div class="cb-header-sub hidden" aria-hidden="true">
                        <span class="status-dot" id="web-chatbot-status-dot"></span>
                        <span id="web-chatbot-status-text"></span>
                    </div>
                </div>
                <div id="web-chatbot-safety-pill" class="safety-pill hidden" title="Website safety status">
                    <span class="safety-pill-icon" aria-hidden="true">✓</span>
                    <span id="web-chatbot-safety-text">Safe</span>
                </div>
                <div class="header-actions">
                    <button id="web-chatbot-theme-toggle" title="Toggle dark mode">
                        <svg id="theme-icon-sun" class="hidden" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                        <svg id="theme-icon-moon" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                    </button>
                    <button id="web-chatbot-reindex" class="hidden" title="Re-index this page" aria-hidden="true" tabindex="-1">
                        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                    </button>
                    <button id="web-chatbot-crawl" class="hidden" title="Crawl whole site" aria-hidden="true" tabindex="-1">
                        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    </button>
                    <button id="web-chatbot-settings" class="hidden" title="Settings" aria-hidden="true" tabindex="-1">
                        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </button>
                    <div id="web-chatbot-mode-picker" class="mode-picker">
                        <button id="web-chatbot-mode-button" class="mode-picker-button" type="button" aria-haspopup="listbox" aria-expanded="false" title="Choose chat mode">
                            <span id="web-chatbot-mode-mark" class="mode-picker-mark" aria-hidden="true">W</span>
                            <span class="mode-picker-text">
                                <span id="web-chatbot-mode-label">Website</span>
                                <span id="web-chatbot-mode-caption">Page chat</span>
                            </span>
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <polyline points="6 9 12 15 18 9"></polyline>
                            </svg>
                        </button>
                        <div id="web-chatbot-mode-menu" class="mode-picker-menu hidden" role="listbox" aria-label="Choose chat mode">
                            <button type="button" class="mode-picker-option active" role="option" aria-selected="true" data-mode="website">
                                <span class="mode-option-mark" aria-hidden="true">W</span>
                                <span class="mode-option-copy">
                                    <span class="mode-option-title">Website</span>
                                    <span class="mode-option-subtitle">Use the current page</span>
                                </span>
                            </button>
                            <button type="button" class="mode-picker-option" role="option" aria-selected="false" data-mode="document">
                                <span class="mode-option-mark" aria-hidden="true">D</span>
                                <span class="mode-option-copy">
                                    <span class="mode-option-title">Document</span>
                                    <span class="mode-option-subtitle">Use uploaded file</span>
                                </span>
                            </button>
                            <button type="button" class="mode-picker-option" role="option" aria-selected="false" data-mode="compare">
                                <span class="mode-option-mark" aria-hidden="true">C</span>
                                <span class="mode-option-copy">
                                    <span class="mode-option-title">Compare</span>
                                    <span class="mode-option-subtitle">File against page</span>
                                </span>
                            </button>
                        </div>
                    </div>
                    <select id="web-chatbot-mode-select" class="hidden" title="Choose chat mode" aria-label="Choose chat mode">
                        <option value="website">Website mode</option>
                        <option value="document">Document mode</option>
                        <option value="compare">Compare mode</option>
                    </select>
                    <button id="web-chatbot-close" title="Minimize"><span aria-hidden="true" style="font-size:20px;line-height:1;">&#x2212;</span></button>
                </div>
            </div>
            <!-- Toolbar: source mode tabs -->
            <div id="web-chatbot-toolbar">
                <div class="cb-mode-tabs" id="cb-mode-tabs">
                    <button class="cb-mode-tab active" data-mode="website">🌐 Website</button>
                    <button class="cb-mode-tab" data-mode="document">📄 Document</button>
                    <button class="cb-mode-tab" data-mode="compare">⚖️ Compare</button>
                </div>
                <span class="cb-toolbar-sep"></span>
                <button id="web-chatbot-crawl-inline" title="Crawl whole site" style="width:30px;height:30px;border:1px solid var(--cb-border);border-radius:6px;background:var(--cb-bg-soft);color:var(--cb-text-muted);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                </button>
                <button id="web-chatbot-chart-inline" title="Create chart" style="width:30px;height:30px;border:1px solid var(--cb-border);border-radius:6px;background:var(--cb-bg-soft);color:var(--cb-text-muted);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="20" x2="20" y2="20"></line><rect x="6" y="10" width="3" height="7"></rect><rect x="11" y="6" width="3" height="11"></rect><rect x="16" y="13" width="3" height="4"></rect></svg>
                </button>
            </div>
            <div id="web-chatbot-control-panel">
                <select id="web-chatbot-scope" class="hidden" title="Website context scope">
                    <option value="page">Current page</option>
                    <option value="site">Whole website</option>
                </select>
                <select id="web-chatbot-source-mode" class="hidden" title="Answer source">
                    <option value="website">Website</option>
                    <option value="document">Document</option>
                    <option value="compare">Compare</option>
                </select>
                <input id="web-chatbot-file" class="hidden" type="file" accept=".pdf,.docx,.txt,.md,.csv,.json,.html,.htm,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/*">
            </div>
            <div id="web-chatbot-document-chip" class="hidden"></div>
            <div id="web-chatbot-webpage-panel" class="hidden">
                <div class="webpage-panel-header">
                    <span class="webpage-panel-icon">
                        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    </span>
                    <span class="webpage-panel-label">Compare with a webpage (Doc B)</span>
                </div>
                <div class="webpage-url-row">
                    <input id="web-chatbot-webpage-url" type="url" placeholder="https://example.com/job-description" autocomplete="off" spellcheck="false" />
                    <button id="web-chatbot-webpage-fetch">Fetch</button>
                </div>
                <span class="webpage-hint">Paste any public URL — the server fetches &amp; extracts its text, then compares it against your uploaded document.</span>
            </div>
            <div id="web-chatbot-compare-tool" class="hidden">
                <div class="compare-compact-bar">
                    <div class="compare-compact-copy">
                        <div class="compare-tool-title">Compare mode active</div>
                        <div id="compare-compact-summary" class="compare-tool-subtitle">Source A and Source B ready when selected</div>
                    </div>
                    <button id="web-chatbot-compare-toggle" type="button">Change sources</button>
                </div>
                <div id="compare-advanced-panel" class="compare-advanced-panel hidden">
                    <div class="compare-tool-head">
                        <div>
                            <div class="compare-tool-title">Compare Tool</div>
                            <div class="compare-tool-subtitle">Separate sources, deterministic comparison</div>
                        </div>
                        <button id="web-chatbot-compare-run" type="button">Run Compare</button>
                    </div>
                    <div class="compare-source-grid">
                        <section class="compare-source-box">
                            <div class="compare-source-title">Source A</div>
                            <div class="compare-source-actions">
                                <button type="button" id="compare-a-upload">Upload document</button>
                                <button type="button" id="compare-a-current">Use current page</button>
                            </div>
                            <div id="compare-a-preview" class="compare-preview">No source selected</div>
                        </section>
                        <section class="compare-source-box">
                            <div class="compare-source-title">Source B</div>
                            <div class="compare-source-actions">
                                <button type="button" id="compare-b-fetch">Fetch URL</button>
                                <button type="button" id="compare-b-upload">Upload document</button>
                                <button type="button" id="compare-b-current">Use current page</button>
                            </div>
                            <input id="web-chatbot-compare-b-file" class="hidden" type="file" accept=".pdf,.docx,.txt,.md,.csv,.json,.html,.htm,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/*">
                            <div id="compare-b-preview" class="compare-preview">No source selected</div>
                        </section>
                    </div>
                    <label class="compare-goal-row hidden">
                        <span>Compare Goal</span>
                        <select id="web-chatbot-compare-goal">
                            <option value="Role fit">Role fit</option>
                            <option value="Feature comparison">Feature comparison</option>
                            <option value="Policy comparison">Policy comparison</option>
                            <option value="Pricing comparison">Pricing comparison</option>
                            <option value="General comparison">General comparison</option>
                        </select>
                    </label>
                </div>
            </div>
            <div id="web-chatbot-settings-panel" class="hidden">
                <div class="settings-tabs">
                    <button id="settings-tab-general" class="settings-tab active" type="button">General</button>
                    <button id="settings-tab-ai" class="settings-tab" type="button">AI Settings</button>
                    <button id="settings-tab-profile" class="settings-tab" type="button">Profile</button>
                </div>
                <div id="settings-content-general" class="settings-content">
                    <label>Pages to crawl <input id="web-chatbot-crawl-limit" type="number" min="1" max="25" value="10"></label>
                    <label><span>Auto-index on open</span> <input id="web-chatbot-auto-index" type="checkbox" checked></label>
                    <button id="web-chatbot-clear">Clear Chat History</button>
                </div>
                <div id="settings-content-ai" class="settings-content hidden">
                    <label><span>Concise answers</span> <input id="web-chatbot-concise" type="checkbox"></label>
                </div>
                <div id="settings-content-profile" class="settings-content hidden">
                    <div class="user-profile-fields">
                        <label class="profile-field-row">Full Name <input id="profile-full-name" type="text" placeholder="John Doe"></label>
                        <label class="profile-field-row">Email <input id="profile-email" type="email" placeholder="john@example.com"></label>
                        <label class="profile-field-row">Phone <input id="profile-phone" type="tel" placeholder="+1234567890"></label>
                        <label class="profile-field-row">Address <input id="profile-address" type="text" placeholder="123 Main St"></label>
                        <label class="profile-field-row">City <input id="profile-city" type="text" placeholder="City"></label>
                        <label class="profile-field-row">State <input id="profile-state" type="text" placeholder="State"></label>
                        <label class="profile-field-row">Country <input id="profile-country" type="text" placeholder="Country"></label>
                        <label class="profile-field-row">DOB <input id="profile-dob" type="date"></label>
                        <label class="profile-field-row">LinkedIn <input id="profile-linkedin" type="url" placeholder="https://linkedin.com/in/..."></label>
                        <label class="profile-field-row">Portfolio <input id="profile-portfolio" type="url" placeholder="https://..."></label>
                        <label class="profile-field-row profile-field-row-full">Custom Fields <textarea id="profile-custom-fields" rows="3" placeholder="github: https://github.com/you&#10;work_authorization: Yes"></textarea></label>
                    </div>
                    <div id="profile-save-status" class="profile-save-status" aria-live="polite"></div>
                </div>
            </div>
            <div id="web-chatbot-messages">
                <div class="message bot">Ready. Ask me anything about this page, or attach a document to compare.</div>
            </div>
            <button id="web-chatbot-scroll-down" class="hidden" type="button" title="Jump to latest message" aria-label="Jump to latest message">
                <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
            <div id="web-chatbot-input-area">
                <button id="web-chatbot-upload" title="Upload document" aria-label="Upload document">
                    <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21.44 11.05 12.25 20.24a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                    </svg>
                </button>
                <div id="web-chatbot-model-picker" class="model-picker">
                    <button id="web-chatbot-model-button" class="model-picker-button" type="button" aria-haspopup="listbox" aria-expanded="false" title="Choose AI model">
                        <span id="web-chatbot-model-mark" class="model-picker-mark" aria-hidden="true">A</span>
                        <span id="web-chatbot-model-label">Auto</span>
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                    <div id="web-chatbot-model-menu" class="model-picker-menu hidden" role="listbox" aria-label="Choose AI model"></div>
                </div>
                <select id="web-chatbot-model" class="hidden" title="Choose AI model">
                    <option value="auto">Auto</option>
                </select>
                <textarea id="web-chatbot-input" placeholder="Ask a question..." autocomplete="off" rows="1"></textarea>
                <button id="web-chatbot-send" title="Send" aria-label="Send">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
            <p class="cb-disclaimer">Aletheia can make mistakes. Verify important information.</p>
        </div>
    `;

    // Elements
    const trigger = document.getElementById('web-chatbot-trigger');
    const chatWindow = document.getElementById('web-chatbot-window');
    const closeBtn = document.getElementById('web-chatbot-close');
    const themeToggleBtn = document.getElementById('web-chatbot-theme-toggle');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');
    const reindexBtn = document.getElementById('web-chatbot-reindex');
    const crawlBtn = document.getElementById('web-chatbot-crawl');
    const settingsBtn = document.getElementById('web-chatbot-settings');
    const clearBtn = document.getElementById('web-chatbot-clear');
    const sendBtn = document.getElementById('web-chatbot-send');
    const input = document.getElementById('web-chatbot-input');
    const messagesContainer = document.getElementById('web-chatbot-messages');
    const scrollDownBtn = document.getElementById('web-chatbot-scroll-down');
    const scopeSelect = document.getElementById('web-chatbot-scope');
    const sourceModeSelect = document.getElementById('web-chatbot-source-mode');
    const modeSelect = document.getElementById('web-chatbot-mode-select');
    const modePicker = document.getElementById('web-chatbot-mode-picker');
    const modeButton = document.getElementById('web-chatbot-mode-button');
    const modeMenu = document.getElementById('web-chatbot-mode-menu');
    const modeLabel = document.getElementById('web-chatbot-mode-label');
    const modeCaption = document.getElementById('web-chatbot-mode-caption');
    const modeMark = document.getElementById('web-chatbot-mode-mark');
    const uploadBtn = document.getElementById('web-chatbot-upload');
    const fileInput = document.getElementById('web-chatbot-file');
    const documentChip = document.getElementById('web-chatbot-document-chip');
    const webpagePanel = document.getElementById('web-chatbot-webpage-panel');
    const webpageUrlInput = document.getElementById('web-chatbot-webpage-url');
    const webpageFetchBtn = document.getElementById('web-chatbot-webpage-fetch');
    const compareToolPanel = document.getElementById('web-chatbot-compare-tool');
    const compareToggleBtn = document.getElementById('web-chatbot-compare-toggle');
    const compareAdvancedPanel = document.getElementById('compare-advanced-panel');
    const compareCompactSummary = document.getElementById('compare-compact-summary');
    const compareRunBtn = document.getElementById('web-chatbot-compare-run');
    const compareGoalSelect = document.getElementById('web-chatbot-compare-goal');
    const compareAUploadBtn = document.getElementById('compare-a-upload');
    const compareACurrentBtn = document.getElementById('compare-a-current');
    const compareBFetchBtn = document.getElementById('compare-b-fetch');
    const compareBUploadBtn = document.getElementById('compare-b-upload');
    const compareBCurrentBtn = document.getElementById('compare-b-current');
    const compareBFileInput = document.getElementById('web-chatbot-compare-b-file');
    const compareAPreview = document.getElementById('compare-a-preview');
    const compareBPreview = document.getElementById('compare-b-preview');
    const settingsPanel = document.getElementById('web-chatbot-settings-panel');
    const crawlLimitInput = document.getElementById('web-chatbot-crawl-limit');
    const modelSelect = document.getElementById('web-chatbot-model');
    const modelPicker = document.getElementById('web-chatbot-model-picker');
    const modelButton = document.getElementById('web-chatbot-model-button');
    const modelMenu = document.getElementById('web-chatbot-model-menu');
    const modelLabel = document.getElementById('web-chatbot-model-label');
    const modelMark = document.getElementById('web-chatbot-model-mark');
    const autoIndexInput = document.getElementById('web-chatbot-auto-index');
    const conciseInput = document.getElementById('web-chatbot-concise');
    const statusDot = document.getElementById('web-chatbot-status-dot');
    const statusText = document.getElementById('web-chatbot-status-text');
    const safetyPill = document.getElementById('web-chatbot-safety-pill');
    const safetyText = document.getElementById('web-chatbot-safety-text');
    const settingsTabs = Array.from(document.querySelectorAll('#web-chatbot-settings-panel .settings-tab'));
    const settingsContents = Array.from(document.querySelectorAll('#web-chatbot-settings-panel .settings-content'));
    const profileSaveStatus = document.getElementById('profile-save-status');
    const profileFields = {
        full_name: document.getElementById('profile-full-name'),
        email: document.getElementById('profile-email'),
        phone: document.getElementById('profile-phone'),
        address: document.getElementById('profile-address'),
        city: document.getElementById('profile-city'),
        state: document.getElementById('profile-state'),
        country: document.getElementById('profile-country'),
        dob: document.getElementById('profile-dob'),
        linkedin: document.getElementById('profile-linkedin'),
        portfolio: document.getElementById('profile-portfolio')
    };
    const profileCustomFieldsInput = document.getElementById('profile-custom-fields');

    let indexedContentHash = '';
    let siteContentHash = '';
    let pageContentHash = '';
    let activeScopeUrl = window.location.href;
    let activeScope = 'page';
    let activeDocumentMode = 'website';
    let uploadedDocument = null;
    let compareSourceA = 'document';
    let compareSourceB = 'fetched';
    let compareSourceBDocument = null;
    let compareAdvancedOpen = false;
    let pendingCompareRequest = null;
    let fetchedWebpageText = '';   // text extracted from a user-supplied URL for compare mode
    let fetchedWebpageUrl = '';
    let latestContent = '';
    let latestContentUrl = '';
    let latestContentHash = '';
    let indexingPromise = null;
    let requestSerial = 0;
    let activeResponseMessage = null;
    let stoppedSerial = 0;
    let activeBackendRequestId = '';
    let backgroundIndexStarted = false;
    let placeholderIndex = 0;
    let placeholderTimer = null;
    const MAX_INDEXED_LINKS = 300;
    const SAFETY_CONTENT_MAX_CHARS = 6000;
    const INDEX_SCHEMA_VERSION = 'visible-content-v3';
    const chatStorageKey = `web-chatbot-history:${window.location.origin}${window.location.pathname}`;
    const settingsStorageKey = 'web-chatbot-settings';
    const userProfileStorageKey = 'web-chatbot-user-profile';
    // Conversation history for adaptive learning (persisted per origin)
    const historyKey = `web-chatbot-conv:${window.location.origin}`;
    const memoryKey = `web-chatbot-memory:${window.location.origin}`;
    const MAX_HISTORY = 10; // Keep last 10 messages for context
    const MAX_MEMORY_TURNS = 8;
    let conversationHistory = JSON.parse(sessionStorage.getItem(historyKey) || '[]');
    let conversationMemory = {};
    try {
        conversationMemory = JSON.parse(sessionStorage.getItem(memoryKey) || '{}');
    } catch (error) {
        conversationMemory = {};
    }
    let safetyVerified = false;
    let proactiveShownForHash = sessionStorage.getItem(`web-chatbot-proactive:${window.location.href}`) || '';
    const pageContentCacheKey = `web-chatbot-page-cache:${window.location.href}`;
    let pageContentCache = {};
    try {
        pageContentCache = JSON.parse(sessionStorage.getItem(pageContentCacheKey) || '{}');
    } catch (error) {
        pageContentCache = {};
    }

    // Theme Logic
    const updateThemeIcons = () => {
        const isDark = container.classList.contains('dark-mode');
        sunIcon.classList.toggle('hidden', !isDark);
        moonIcon.classList.toggle('hidden', isDark);
    };
    updateThemeIcons();

    themeToggleBtn.onclick = () => {
        container.classList.toggle('dark-mode');
        localStorage.setItem('web-chatbot-theme', container.classList.contains('dark-mode') ? 'dark' : 'light');
        updateThemeIcons();
    };

    // Auto-switch theme when the OS/browser theme changes (e.g. day -> night),
    // but only if the user has not manually chosen a theme via the toggle above.
    if (window.matchMedia) {
        const systemThemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleSystemThemeChange = (event) => {
            if (localStorage.getItem('web-chatbot-theme')) return; // manual override in place
            container.classList.toggle('dark-mode', event.matches);
            updateThemeIcons();
        };
        if (systemThemeQuery.addEventListener) {
            systemThemeQuery.addEventListener('change', handleSystemThemeChange);
        } else if (systemThemeQuery.addListener) {
            systemThemeQuery.addListener(handleSystemThemeChange);
        }
    }

    const checkWebsiteSafety = async () => {
        if (safetyVerified) return true;
        safetyPill.classList.remove('hidden', 'safe', 'warning', 'harmful');
        safetyPill.classList.add('checking');
        safetyText.textContent = 'Checking';
        
        try {
            const content = getCachedPageContent().slice(0, SAFETY_CONTENT_MAX_CHARS);
            const result = await sendBackendMessage('fetchSafety', {
                url: window.location.href,
                content: content
            });

            if (result.status === 'safe') {
                safetyPill.classList.remove('checking', 'warning', 'harmful');
                safetyPill.classList.add('safe');
                safetyPill.title = result.reason || 'Website safety check passed.';
                safetyText.textContent = 'Safe';
                safetyVerified = true;
                return true;
            } else {
                const isHarmful = result.status === 'harmful';
                safetyPill.classList.remove('checking', 'safe', 'warning', 'harmful');
                safetyPill.classList.add(isHarmful ? 'harmful' : 'warning');
                safetyPill.title = result.reason || 'Website safety warning.';
                safetyText.textContent = isHarmful ? 'Risk' : 'Warn';
                const warningCard = document.createElement('div');
                warningCard.className = 'safety-warning-card';
                warningCard.innerHTML = `
                    <h4>${isHarmful ? '⚠️ Harmful Website Detected' : '⚡ Suspicious Website Warning'}</h4>
                    <p>${result.reason}</p>
                    <div class="safety-actions">
                        <button class="btn-proceed">Proceed Anyway</button>
                        <button class="btn-cancel">Exit Chat</button>
                    </div>
                `;
                messagesContainer.appendChild(warningCard);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                return new Promise((resolve) => {
                    warningCard.querySelector('.btn-proceed').onclick = () => {
                        warningCard.remove();
                        addMessage('Proceeding with caution...', 'bot', { persist: false });
                        safetyVerified = true;
                        resolve(true);
                    };
                    warningCard.querySelector('.btn-cancel').onclick = () => {
                        chatWindow.classList.add('hidden');
                        resolve(false);
                    };
                });
            }
        } catch (error) {
            console.debug("Safety check skipped:", error);
            safetyPill.classList.add('hidden');
            safetyPill.classList.remove('checking', 'safe', 'warning', 'harmful');
            safetyVerified = true;
            return true;
        }
    };

    // Toggle Window
    trigger.onclick = async () => {
        chatWindow.classList.toggle('hidden');
        trigger.classList.toggle('is-open', !chatWindow.classList.contains('hidden'));
        if (!chatWindow.classList.contains('hidden')) {
            checkBackendHealth();
            const proceed = await checkWebsiteSafety();
            if (!proceed) return;

            if (autoIndexInput.checked) {
                ensureIndexed().then((contentHash) => {
                    showProactiveIntro(contentHash);
                }).catch((error) => {
                    console.warn('Page pre-index failed:', error);
                    showProactiveIntro('');
                });
            } else {
                showProactiveIntro('');
            }
            input.focus();
        }
    };
    closeBtn.onclick = () => {
        chatWindow.classList.add('hidden');
        trigger.classList.remove('is-open');
    };

    const escapeHtml = (value) => String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

    const escapeAttribute = (value) => escapeHtml(value)
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

    const parseMermaidNode = (raw) => {
        const value = String(raw || '').trim();
        // Handle parallelogram: A[/label/] or A[\\label\\]
        const paraMatch = value.match(/^([A-Za-z0-9_]+)\s*\[[\/\\](.+?)[\/\\]\]$/);
        if (paraMatch) return { id: paraMatch[1], label: paraMatch[2].trim(), shape: 'parallelogram' };
        // Handle rounded terminal: A([label])
        const termMatch = value.match(/^([A-Za-z0-9_]+)\s*\(\[(.+?)\]\)$/);
        if (termMatch) return { id: termMatch[1], label: termMatch[2].trim(), shape: 'round' };
        // Standard shapes: A[label] A(label) A{label} A((label))
        const match = value.match(/^([A-Za-z0-9_]+)\s*(?:([\[\(\{])(.+?)([\]\)\}]))?$/);
        if (!match) return { id: value.replace(/[^A-Za-z0-9_]/g, '_') || 'node', label: value || 'Step', shape: 'rect' };
        const shapeMap = { '[': 'rect', '(': 'round', '{': 'diamond' };
        return {
            id: match[1],
            label: (match[3] || match[1]).replace(/^["']|["']$/g, '').trim(),
            shape: shapeMap[match[2]] || 'rect'
        };
    };

    const parseMermaidSubgraph = (raw, index) => {
        const value = String(raw || '').trim();
        const match = value.match(/^subgraph\s+(.+)$/i);
        if (!match) return null;

        const definition = match[1].trim();
        const bracketLabel = definition.match(/^(?:([A-Za-z0-9_]+)\s*)?\[(.+)\]$/);
        const label = (bracketLabel ? bracketLabel[2] : definition)
            .replace(/^["']|["']$/g, '')
            .trim() || 'Group';
        const idBase = (bracketLabel?.[1] || label).replace(/[^A-Za-z0-9_]/g, '_') || 'group';
        return {
            id: `subgraph_${index}_${idBase}`,
            label,
            nodes: new Set()
        };
    };

    const wrapFlowLabel = (label, maxChars = 22, maxLines = 4) => {
        const words = String(label || 'Step').replace(/\s+/g, ' ').trim().split(' ');
        const lines = [];
        let current = '';

        words.forEach((word) => {
            const next = current ? `${current} ${word}` : word;
            if (next.length <= maxChars) {
                current = next;
                return;
            }
            if (current) lines.push(current);
            current = word.length > maxChars ? `${word.slice(0, maxChars - 1)}.` : word;
        });

        if (current) lines.push(current);
        if (lines.length <= maxLines) return lines;

        const clipped = lines.slice(0, maxLines);
        clipped[maxLines - 1] = `${clipped[maxLines - 1].slice(0, Math.max(4, maxChars - 3))}...`;
        return clipped;
    };

    const renderFlowText = (label, x, y, maxChars = 22, maxLines = 4, className = '') => {
        const lines = wrapFlowLabel(label, maxChars, maxLines);
        const lineHeight = className === 'flow-diagram-edge-label' ? 12 : 14;
        const startY = y - ((lines.length - 1) * lineHeight) / 2;
        const classAttr = className ? ` class="${className}"` : '';
        const tspans = lines
            .map((line, index) => `<tspan x="${x}" y="${startY + index * lineHeight}">${escapeHtml(line)}</tspan>`)
            .join('');
        return `<text${classAttr} x="${x}" y="${y}" text-anchor="middle">${tspans}</text>`;
    };

    const normalizeFlowNodeType = (type) => {
        const normalized = String(type || 'process').toLowerCase().trim();
        return ['terminal', 'input', 'process', 'decision', 'output'].includes(normalized)
            ? normalized
            : 'process';
    };

    const hasGenericFlowchartTemplate = (diagram) => {
        const topic = String(diagram?.diagram_topic || '').toLowerCase();
        const basis = Array.isArray(diagram?.context_basis) ? diagram.context_basis.join(' ').toLowerCase() : '';
        const labels = (diagram?.nodes || []).map((node) => String(node.label || '').toLowerCase());
        const joinedLabels = labels.join(' ');

        // Expanded list of placeholder labels common LLMs use when ignoring context
        const genericTerms = [
            'submit login form', 'credentials valid', 'create authenticated session',
            'open dashboard', 'show login error', 'upload file', 'process data',
            'send notification', 'checkout', 'payment valid',
            'initialize system', 'validate input', 'process request',
            'return response', 'handle error', 'fetch data', 'store result',
            'display result', 'user action', 'system response', 'api call',
            'database query', 'render page', 'log event', 'retry logic',
            'error handling', 'success response', 'failure response',
            'begin process', 'end process', 'step one', 'step two', 'step three',
            'next step', 'previous step', 'main process', 'sub process',
        ];
        const genericHits = genericTerms.filter((term) => joinedLabels.includes(term)).length;

        const weakTopic = !topic || [
            'project', 'flowchart', 'process', 'system', 'website',
            'application', 'app', 'workflow', 'pipeline', 'diagram'
        ].includes(topic.trim());
        const weakBasis = !basis || basis.includes('specific fact from context');

        // Generic hit threshold: 2+ generic labels = reject
        if (genericHits >= 2) return true;
        // Weak topic AND weak basis AND 4+ nodes = almost certainly a template
        if (weakTopic && weakBasis && labels.length >= 4) return true;

        return false;
    };

    // Check node labels overlap with actual page content
    // Returns true if the diagram appears grounded in real page content
    const isFlowchartGrounded = (diagram, pageText) => {
        if (!pageText || !diagram?.nodes?.length) return true; // can't check = allow
        const text = pageText.toLowerCase();
        const stopWords = new Set([
            'the', 'and', 'for', 'are', 'this', 'that', 'with', 'from',
            'have', 'will', 'been', 'has', 'was', 'not', 'but', 'all'
        ]);
        let matchCount = 0;
        diagram.nodes.forEach((node) => {
            const words = String(node.label || '').toLowerCase()
                .split(/\s+/)
                .filter((w) => w.length > 3 && !stopWords.has(w));
            if (words.some((w) => text.includes(w))) matchCount++;
        });
        const overlapRatio = matchCount / diagram.nodes.length;
        return overlapRatio >= 0.2; // at least 20% of nodes have a word in the page
    };

    const stripEmojis = (str) => {
        if (!str) return '';
        try {
            return str.replace(/[\u2600-\u27BF]|[\u{1F300}-\u{1F6FF}]|[\u{1F900}-\u{1F9FF}]/gu, '')
                      .replace(/[\p{Extended_Pictographic}\p{Emoji_Component}\p{Emoji_Presentation}\p{Emoji_Modifier}\p{Emoji_Modifier_Base}]/gu, '')
                      .replace(/\s+/g, ' ')
                      .trim();
        } catch (e) {
            return str.replace(/[\u2600-\u27BF]|[\u{1F300}-\u{1F6FF}]/gu, '').replace(/\s+/g, ' ').trim();
        }
    };

    const parseReactFlowJson = (code) => {
        try {
            const parsed = JSON.parse(String(code || '').trim());
            const rawNodes = Array.isArray(parsed.nodes) ? parsed.nodes : [];
            const rawEdges = Array.isArray(parsed.edges) ? parsed.edges : [];
            if (!rawNodes.length || !rawEdges.length) return null;

            const nodeIds = new Set();
            const nodes = rawNodes
                .map((node, index) => {
                    const id = String(node.id || `node_${index + 1}`).replace(/[^A-Za-z0-9_-]/g, '_');
                    const label = stripEmojis(String(node.label || node.data?.label || '').replace(/\s+/g, ' ').trim());
                    if (!id || !label || /^[A-Z]$/i.test(label)) return null;
                    nodeIds.add(id);
                    return {
                        id,
                        label,
                        description: stripEmojis(String(node.description || node.data?.description || '').replace(/\s+/g, ' ').trim()),
                        type: normalizeFlowNodeType(node.type),
                        phase: stripEmojis(String(node.phase || node.data?.phase || '').replace(/\s+/g, ' ').trim())
                    };
                })
                .filter(Boolean)
                .slice(0, 24);

            const validIds = new Set(nodes.map((node) => node.id));
            const edges = rawEdges
                .map((edge) => ({
                    from: String(edge.source || edge.from || '').replace(/[^A-Za-z0-9_-]/g, '_'),
                    to: String(edge.target || edge.to || '').replace(/[^A-Za-z0-9_-]/g, '_'),
                    label: stripEmojis(String(edge.label || edge.data?.label || '').replace(/\s+/g, ' ').trim())
                }))
                .filter((edge) => validIds.has(edge.from) && validIds.has(edge.to) && edge.from !== edge.to)
                .slice(0, 36);

            if (!nodes.length || !edges.length) return null;
            const diagram = {
                diagram_topic: String(parsed.diagram_topic || '').trim(),
                context_basis: Array.isArray(parsed.context_basis) ? parsed.context_basis.slice(0, 6) : [],
                layout: String(parsed.layout || 'TD').toUpperCase() === 'LR' ? 'LR' : 'TD',
                nodes,
                edges
            };
            return { ...diagram };
        } catch (error) {
            return null;
        }
    };

    const renderReactFlowJsonFlowchart = (code) => {
        const diagram = parseReactFlowJson(code);
        if (!diagram) {
            return `<pre class="message-code" data-language="json"><code>${escapeHtml(String(code || '').trim())}</code></pre>`;
        }

        const nodeWidth = 184;
        const nodeHeight = 82;
        const xGap = 42;
        const yGap = 54;
        const byId = new Map(diagram.nodes.map((node) => [node.id, node]));
        const indegree = {};
        const outgoing = {};
        diagram.nodes.forEach((node) => {
            indegree[node.id] = 0;
            outgoing[node.id] = [];
        });
        diagram.edges.forEach((edge) => {
            indegree[edge.to] = (indegree[edge.to] || 0) + 1;
            outgoing[edge.from] = outgoing[edge.from] || [];
            outgoing[edge.from].push(edge.to);
        });

        const levels = {};
        const queue = diagram.nodes.filter((node) => !indegree[node.id]).map((node) => node.id);
        if (!queue.length) queue.push(diagram.nodes[0].id);
        queue.forEach((id) => { levels[id] = 0; });
        while (queue.length) {
            const id = queue.shift();
            (outgoing[id] || []).forEach((next) => {
                const nextLevel = (levels[id] || 0) + 1;
                if (levels[next] === undefined || nextLevel > levels[next]) {
                    levels[next] = nextLevel;
                    queue.push(next);
                }
            });
        }
        diagram.nodes.forEach((node) => {
            if (levels[node.id] === undefined) levels[node.id] = 0;
        });

        const layerMap = {};
        diagram.nodes.forEach((node) => {
            const level = levels[node.id];
            layerMap[level] = layerMap[level] || [];
            layerMap[level].push(node.id);
        });

        const layers = Object.keys(layerMap).map(Number).sort((a, b) => a - b);
        const maxColumns = Math.max(...Object.values(layerMap).map((items) => items.length));
        const width = Math.max(340, maxColumns * (nodeWidth + xGap) - xGap + 56);
        const height = Math.max(190, layers.length * (nodeHeight + yGap) - yGap + 58);
        const positions = {};

        layers.forEach((level, rowIndex) => {
            const ids = layerMap[level];
            const totalWidth = ids.length * nodeWidth + (ids.length - 1) * xGap;
            const startX = (width - totalWidth) / 2;
            ids.forEach((id, columnIndex) => {
                positions[id] = {
                    x: startX + columnIndex * (nodeWidth + xGap),
                    y: 28 + rowIndex * (nodeHeight + yGap)
                };
            });
        });

        const phases = [];
        const phaseMap = new Map();
        diagram.nodes.forEach((node) => {
            if (!node.phase) return;
            const phaseLabel = stripEmojis(node.phase);
            if (!phaseLabel) return;
            if (!phaseMap.has(phaseLabel)) {
                const group = { label: phaseLabel, ids: [] };
                phaseMap.set(phaseLabel, group);
                phases.push(group);
            }
            phaseMap.get(phaseLabel).ids.push(node.id);
        });

        const subgraphSvg = phases.map((phase) => {
            const groupedPositions = phase.ids.map((id) => positions[id]).filter(Boolean);
            if (!groupedPositions.length) return '';
            const minX = Math.min(...groupedPositions.map((pos) => pos.x));
            const minY = Math.min(...groupedPositions.map((pos) => pos.y));
            const maxX = Math.max(...groupedPositions.map((pos) => pos.x + nodeWidth));
            const maxY = Math.max(...groupedPositions.map((pos) => pos.y + nodeHeight));
            const x = Math.max(4, minX - 14);
            const y = Math.max(4, minY - 24);
            return `
                <g class="flow-diagram-subgraph">
                    <rect class="flow-diagram-subgraph-fill" x="${x}" y="${y}" width="${Math.min(width - x - 4, maxX - minX + 28)}" height="${Math.min(height - y - 4, maxY - minY + 40)}" rx="12" />
                    <text class="flow-diagram-subgraph-label" x="${x + 12}" y="${y + 16}">${escapeHtml(phase.label)}</text>
                </g>
            `;
        }).join('');

        const edgeSvg = diagram.edges.map((edge) => {
            const from = positions[edge.from];
            const to = positions[edge.to];
            if (!from || !to) return '';
            const x1 = from.x + nodeWidth / 2;
            const y1 = from.y + nodeHeight;
            const x2 = to.x + nodeWidth / 2;
            const y2 = to.y;
            const midY = y1 + Math.max(20, (y2 - y1) / 2);
            const pathD = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
            const label = edge.label
                ? renderFlowText(edge.label, (x1 + x2) / 2, midY - 8, 18, 2, 'flow-diagram-edge-label')
                : '';
            return `
                <path class="flow-diagram-edge-glow" d="${pathD}" pathLength="120" />
                <path class="flow-diagram-edge" d="${pathD}" marker-end="url(#flow-arrow)" />
                ${label}
            `;
        }).join('');

        const nodeSvg = diagram.nodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return '';
            const cx = pos.x + nodeWidth / 2;
            const cy = pos.y + nodeHeight / 2;
            let shape;
            if (node.type === 'decision') {
                shape = `<polygon class="flow-diagram-node-shape flow-diagram-node-decision" points="${cx},${pos.y} ${pos.x + nodeWidth},${cy} ${cx},${pos.y + nodeHeight} ${pos.x},${cy}" />`;
            } else if (node.type === 'input' || node.type === 'output') {
                const skew = 16;
                shape = `<polygon class="flow-diagram-node-shape flow-diagram-node-io" points="${pos.x + skew},${pos.y} ${pos.x + nodeWidth},${pos.y} ${pos.x + nodeWidth - skew},${pos.y + nodeHeight} ${pos.x},${pos.y + nodeHeight}" />`;
            } else {
                shape = `<rect class="flow-diagram-node-shape flow-diagram-node-${node.type}" x="${pos.x}" y="${pos.y}" width="${nodeWidth}" height="${nodeHeight}" rx="${node.type === 'terminal' ? 22 : 8}" />`;
            }
            const description = node.description && node.description !== node.label
                ? `<title>${escapeHtml(node.description)}</title>`
                : '';
            return `<g class="flow-diagram-node">${description}${shape}${renderFlowText(node.label, cx, cy)}</g>`;
        }).join('');

        return `
            <div class="flow-diagram-wrap flow-diagram-json" role="button" tabindex="0" aria-label="Open flow diagram larger" title="Click to enlarge">
                <svg class="flow-diagram-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Flow diagram">
                    <defs>
                        <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" class="flow-diagram-arrow"></path>
                        </marker>
                    </defs>
                    ${subgraphSvg}
                    ${edgeSvg}
                    ${nodeSvg}
                </svg>
                <div class="flow-diagram-actions">
                    <span class="flow-diagram-expand-hint">JSON flow</span>
                    <span class="flow-diagram-downloads">
                        <button type="button" class="flow-diagram-download" title="Download flowchart as SVG" aria-label="Download flowchart as SVG"><span>SVG</span></button>
                        <button type="button" class="flow-diagram-download-png" title="Download flowchart as PNG" aria-label="Download flowchart as PNG"><span>PNG</span></button>
                        <button type="button" class="flow-diagram-regenerate" title="Regenerate diagram with a different layout" aria-label="Regenerate diagram with a different layout"><span>Regenerate</span></button>
                    </span>
                </div>
                <details class="flow-diagram-code"><summary>JSON</summary><pre>${escapeHtml(String(code || '').trim())}</pre></details>
            </div>
        `;
    };

    const renderMermaidFlowchart = (code) => {
        const lines = String(code || '')
            .replace(/\r\n/g, '\n')
            .split('\n')
            .map((line) => line.trim())
            .filter((line) => line && !line.startsWith('%%'));
        if (!lines.length || !/^(graph|flowchart)\s+/i.test(lines[0])) {
            return `<pre class="message-code" data-language="mermaid"><code>${escapeHtml(code.trim())}</code></pre>`;
        }

        const nodes = new Map();
        const edges = [];
        const subgraphs = [];
        let activeSubgraph = null;

        lines.slice(1).forEach((line, index) => {
            const subgraph = parseMermaidSubgraph(line, index);
            if (subgraph) {
                activeSubgraph = subgraph;
                subgraphs.push(subgraph);
                return;
            }
            if (/^end$/i.test(line)) {
                activeSubgraph = null;
                return;
            }

            // Robust edge match: handles labels like A[text] -->|label| B{text}
            const edgeMatch = line.match(/^(.+?)\s*-{1,2}>(?:\|([^|]*)\|)?\s*(.+)$/);
            if (!edgeMatch) return;

            const from = parseMermaidNode(edgeMatch[1].trim());
            const to   = parseMermaidNode(edgeMatch[3].trim());
            nodes.set(from.id, { ...(nodes.get(from.id) || {}), ...from });
            nodes.set(to.id,   { ...(nodes.get(to.id)   || {}), ...to   });
            if (activeSubgraph) {
                activeSubgraph.nodes.add(from.id);
                activeSubgraph.nodes.add(to.id);
            }
            edges.push({ from: from.id, to: to.id, label: (edgeMatch[2] || '').trim() });
        });

        if (!nodes.size || !edges.length) {
            return `<pre class="message-code" data-language="mermaid"><code>${escapeHtml(code.trim())}</code></pre>`;
        }

        const indegree = {};
        const outgoing = {};
        nodes.forEach((_, id) => {
            indegree[id] = 0;
            outgoing[id] = [];
        });
        edges.forEach((edge) => {
            indegree[edge.to] = (indegree[edge.to] || 0) + 1;
            outgoing[edge.from] = outgoing[edge.from] || [];
            outgoing[edge.from].push(edge.to);
        });

        const levels = {};
        const queue = Array.from(nodes.keys()).filter((id) => !indegree[id]);
        if (!queue.length) queue.push(Array.from(nodes.keys())[0]);
        queue.forEach((id) => { levels[id] = 0; });
        while (queue.length) {
            const id = queue.shift();
            (outgoing[id] || []).forEach((next) => {
                const nextLevel = (levels[id] || 0) + 1;
                if (levels[next] === undefined || nextLevel > levels[next]) {
                    levels[next] = nextLevel;
                    queue.push(next);
                }
            });
        }
        nodes.forEach((_, id) => {
            if (levels[id] === undefined) levels[id] = 0;
        });

        const layerMap = {};
        nodes.forEach((_, id) => {
            const level = levels[id];
            layerMap[level] = layerMap[level] || [];
            layerMap[level].push(id);
        });

        const nodeWidth = 176;
        const nodeHeight = 84;
        const xGap = 96;
        const yGap = 42;
        const layers = Object.keys(layerMap).map(Number).sort((a, b) => a - b);
        const maxRows = Math.max(...Object.values(layerMap).map((items) => items.length));
        const width = Math.max(320, layers.length * (nodeWidth + xGap) - xGap + 48);
        const height = Math.max(160, maxRows * (nodeHeight + yGap) - yGap + 44);
        const positions = {};

        layers.forEach((level, layerIndex) => {
            const ids = layerMap[level];
            const totalHeight = ids.length * nodeHeight + (ids.length - 1) * yGap;
            const startY = (height - totalHeight) / 2;
            ids.forEach((id, rowIndex) => {
                positions[id] = {
                    x: 24 + layerIndex * (nodeWidth + xGap),
                    y: startY + rowIndex * (nodeHeight + yGap)
                };
            });
        });

        const subgraphSvg = subgraphs.map((subgraph) => {
            const groupedPositions = Array.from(subgraph.nodes)
                .map((id) => positions[id])
                .filter(Boolean);
            if (!groupedPositions.length) return '';

            const minX = Math.min(...groupedPositions.map((pos) => pos.x));
            const minY = Math.min(...groupedPositions.map((pos) => pos.y));
            const maxX = Math.max(...groupedPositions.map((pos) => pos.x + nodeWidth));
            const maxY = Math.max(...groupedPositions.map((pos) => pos.y + nodeHeight));
            const x = Math.max(4, minX - 16);
            const y = Math.max(4, minY - 28);
            const boxWidth = Math.min(width - x - 4, maxX - minX + 32);
            const boxHeight = Math.min(height - y - 4, maxY - minY + 44);

            return `
                <g class="flow-diagram-subgraph">
                    <rect class="flow-diagram-subgraph-fill" x="${x}" y="${y}" width="${boxWidth}" height="${boxHeight}" rx="12" />
                    <text class="flow-diagram-subgraph-label" x="${x + 12}" y="${y + 17}">${escapeHtml(subgraph.label)}</text>
                </g>
            `;
        }).join('');

        const edgeSvg = edges.map((edge) => {
            const from = positions[edge.from];
            const to = positions[edge.to];
            if (!from || !to) return '';
            const x1 = from.x + nodeWidth;
            const y1 = from.y + nodeHeight / 2;
            const x2 = to.x;
            const y2 = to.y + nodeHeight / 2;
            const midX = x1 + Math.max(28, (x2 - x1) / 2);
            const pathD = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
            const label = edge.label
                ? renderFlowText(edge.label, (x1 + x2) / 2, (y1 + y2) / 2 - 10, 18, 2, 'flow-diagram-edge-label')
                : '';
            return `
                <path class="flow-diagram-edge-glow" d="${pathD}" pathLength="120" />
                <path class="flow-diagram-edge" d="${pathD}" marker-end="url(#flow-arrow)" />
                ${label}
            `;
        }).join('');

        const nodeSvg = Array.from(nodes.values()).map((node) => {
            const pos = positions[node.id];
            if (!pos) return '';
            const cx = pos.x + nodeWidth / 2;
            const cy = pos.y + nodeHeight / 2;
            let shape;
            if (node.shape === 'diamond') {
                shape = `<polygon class="flow-diagram-node-shape" points="${cx},${pos.y} ${pos.x + nodeWidth},${cy} ${cx},${pos.y + nodeHeight} ${pos.x},${cy}" />`;
            } else if (node.shape === 'parallelogram') {
                const skew = 16;
                shape = `<polygon class="flow-diagram-node-shape" points="${pos.x + skew},${pos.y} ${pos.x + nodeWidth},${pos.y} ${pos.x + nodeWidth - skew},${pos.y + nodeHeight} ${pos.x},${pos.y + nodeHeight}" />`;
            } else {
                shape = `<rect class="flow-diagram-node-shape" x="${pos.x}" y="${pos.y}" width="${nodeWidth}" height="${nodeHeight}" rx="${node.shape === 'round' ? 18 : 8}" />`;
            }
            return `<g class="flow-diagram-node">${shape}${renderFlowText(node.label, cx, cy)}</g>`;
        }).join('');

        return `
            <div class="flow-diagram-wrap" role="button" tabindex="0" aria-label="Open flow diagram larger" title="Click to enlarge">
                <svg class="flow-diagram-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Flow diagram">
                    <defs>
                        <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" class="flow-diagram-arrow"></path>
                        </marker>
                    </defs>
                    ${subgraphSvg}
                    ${edgeSvg}
                    ${nodeSvg}
                </svg>
                <div class="flow-diagram-actions">
                    <span class="flow-diagram-expand-hint">Click to enlarge</span>
                    <span class="flow-diagram-downloads">
                        <button type="button" class="flow-diagram-download" title="Download flowchart as SVG" aria-label="Download flowchart as SVG">
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            <span>SVG</span>
                        </button>
                        <button type="button" class="flow-diagram-download-png" title="Download flowchart as PNG" aria-label="Download flowchart as PNG">
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            <span>PNG</span>
                        </button>
                        <button type="button" class="flow-diagram-regenerate" title="Regenerate diagram with a different layout" aria-label="Regenerate diagram with a different layout">
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                <polyline points="23 4 23 10 17 10"></polyline>
                                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                            </svg>
                            <span>Regenerate</span>
                        </button>
                    </span>
                </div>
                <details class="flow-diagram-code"><summary>Mermaid</summary><pre>${escapeHtml(code.trim())}</pre></details>
            </div>
        `;
    };

    const shortDisplayUrl = (value, maxLength = 54) => {
        const raw = String(value || '').trim();
        if (!raw) return '';

        if (raw.startsWith('mailto:')) return raw.replace(/^mailto:/i, '');
        if (raw.startsWith('tel:')) return raw.replace(/^tel:/i, '');

        try {
            const url = new URL(raw, window.location.href);
            const path = `${url.pathname}${url.search}`.replace(/\/$/, '');
            const display = `${url.hostname.replace(/^www\./, '')}${path && path !== '/' ? path : ''}`;
            return display.length > maxLength ? `${display.slice(0, maxLength - 1)}...` : display;
        } catch (error) {
            return raw.length > maxLength ? `${raw.slice(0, maxLength - 1)}...` : raw;
        }
    };

    const IMPORTANT_DATE_PATTERN = /\b(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),?\s+\d{4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*|\s+)\d{4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b/gi;

    const highlightImportantDatesInHtml = (html) => {
        let skipInlineHighlight = false;
        return String(html || '')
            .split(/(<[^>]+>)/g)
            .map((part) => {
                if (!part) return part;
                if (part.startsWith('<')) {
                    if (/^<(a|code)\b/i.test(part)) skipInlineHighlight = true;
                    if (/^<\/(a|code)>/i.test(part)) skipInlineHighlight = false;
                    return part;
                }
                if (skipInlineHighlight) return part;
                return part.replace(IMPORTANT_DATE_PATTERN, '<span class="important-date">$&</span>');
            })
            .join('');
    };

    const formatInlineBotText = (text, options = {}) => {
        let html = escapeHtml(text)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

        // Parse markdown-style links [text](url) — always enabled since they are explicit
        html = html.replace(
            /\[([^\]]+)\]\((https?:\/\/[^)\s]+|mailto:[^)\s]+|tel:[^)\s]+)\)/g,
            (_, linkText, url) => `<a href="${escapeAttribute(url)}" target="_blank" rel="noopener noreferrer" title="${escapeAttribute(url)}">${linkText}</a>`
        );

        if (options.linkify) {
            // Auto-linkify bare URLs that are NOT already inside an <a> tag
            html = html.replace(
                /(https?:\/\/[^\s<]+|mailto:[^\s<]+|tel:[^\s<]+)/g,
                (match, _url, offset) => {
                    // Check if this URL is already inside an href="..." or >...</a>
                    const before = html.slice(Math.max(0, offset - 200), offset);
                    if (/href=["'][^"']*$/.test(before) || /<a\s[^>]*>[^<]*$/.test(before)) return match;
                    return `<a href="${escapeAttribute(match)}" target="_blank" rel="noopener noreferrer" title="${escapeAttribute(match)}">${escapeHtml(shortDisplayUrl(match))}</a>`;
                }
            );
        }

        return highlightImportantDatesInHtml(html);
    };

    const isTableSeparator = (line) => /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
    const isTableRow = (line) => line.includes('|') && line.split('|').filter((cell) => cell.trim()).length >= 2;
    const splitTableRow = (line) => line
        .trim()
        .replace(/^\|/, '')
        .replace(/\|$/, '')
        .split('|')
        .map((cell) => cell.trim());

    const renderTable = (rows, options = {}) => {
        if (rows.length < 2) return '';
        const header = splitTableRow(rows[0]);
        const tableClass = header.some((cell) => ['Impact', 'Source A', 'Source B', 'Reason'].includes(cell))
            ? 'message-table-wrap compare-result-table-wrap'
            : 'message-table-wrap';
        const allBodyRows = rows.slice(isTableSeparator(rows[1]) ? 2 : 1).map(splitTableRow).filter(row => row.length);
        const MAX_DISPLAY_ROWS = 5;
        const isTruncated = allBodyRows.length > MAX_DISPLAY_ROWS;
        const displayRows = isTruncated ? allBodyRows.slice(0, MAX_DISPLAY_ROWS) : allBodyRows;

        const headerHtml = header.map((cell) => `<th>${formatInlineBotText(cell, options)}</th>`).join('');
        const getBodyHtml = (rws) => rws
            .map((row) => `<tr>${header.map((_, index) => `<td>${formatInlineBotText(row[index] || '', options)}</td>`).join('')}</tr>`)
            .join('');

        let html = `<div class="${tableClass}${isTruncated ? ' is-truncated' : ''}" role="button" tabindex="0" aria-label="Open table preview" title="Open table preview">`;
        html += `<table><thead><tr>${headerHtml}</tr></thead><tbody>${getBodyHtml(displayRows)}</tbody></table>`;
        if (isTruncated) {
            html += `<div class="table-truncate-hint">Showing ${MAX_DISPLAY_ROWS} of ${allBodyRows.length} rows. Click to see all.</div>`;
            html += `<table class="full-table-source hidden" style="display:none" aria-hidden="true"><thead><tr>${headerHtml}</tr></thead><tbody>${getBodyHtml(allBodyRows)}</tbody></table>`;
        }
        html += `</div>`;
        return html;
    };

    const parseChartJson = (text) => {
        try {
            const data = JSON.parse(String(text || '').trim());
            if (!data || typeof data !== 'object') return null;
            const type = String(data.type || '').toLowerCase();
            if (!['bar', 'horizontal_bar', 'radar', 'pie', 'donut', 'line'].includes(type)) return null;
            if (!Array.isArray(data.labels) || !Array.isArray(data.datasets) || !data.datasets.length) return null;
            return data;
        } catch (_) {
            return null;
        }
    };

    const renderInfoChart = (chart) => {
        const labels = (chart.labels || []).map((label) => String(label || '').slice(0, 34));
        const dataset = (chart.datasets || [])[0] || {};
        const values = (dataset.data || []).map((value) => Number(value) || 0).slice(0, labels.length);
        if (!labels.length || values.length !== labels.length) return '';
        const type = String(chart.type || 'bar').toLowerCase();
        const maxValue = Math.max(1, ...values.map((value) => Math.abs(value)));
        const colors = ['#2563eb', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#64748b'];
        const width = 360;
        const height = type === 'horizontal_bar' ? Math.max(220, labels.length * 38 + 70) : 260;
        const esc = escapeHtml;
        let svg = '';

        if (type === 'horizontal_bar') {
            const left = 112;
            const chartWidth = 210;
            svg = values.map((value, index) => {
                const y = 48 + index * 38;
                const barWidth = Math.max(4, (Math.abs(value) / maxValue) * chartWidth);
                return `
                    <text x="8" y="${y + 15}" class="info-chart-label">${esc(labels[index])}</text>
                    <rect x="${left}" y="${y}" width="${barWidth}" height="20" rx="5" fill="${colors[index % colors.length]}"></rect>
                    <text x="${left + barWidth + 6}" y="${y + 15}" class="info-chart-value">${esc(String(Math.round(value)))}</text>
                `;
            }).join('');
        } else if (type === 'line') {
            const points = values.map((value, index) => {
                const x = 42 + (index * 270 / Math.max(1, values.length - 1));
                const y = 205 - ((value / maxValue) * 145);
                return { x, y, value, label: labels[index] };
            });
            const polyline = points.map((point) => `${point.x},${point.y}`).join(' ');
            svg = `
                <line x1="36" y1="210" x2="328" y2="210" class="info-chart-axis"></line>
                <line x1="36" y1="54" x2="36" y2="210" class="info-chart-axis"></line>
                <polyline points="${polyline}" class="info-chart-line"></polyline>
                ${points.map((point, index) => `
                    <circle cx="${point.x}" cy="${point.y}" r="4.5" fill="${colors[index % colors.length]}"></circle>
                    <text x="${point.x}" y="${point.y - 9}" text-anchor="middle" class="info-chart-value">${esc(String(Math.round(point.value)))}</text>
                `).join('')}
            `;
        } else if (type === 'radar') {
            const cx = 180;
            const cy = 135;
            const radius = 82;
            const points = values.map((value, index) => {
                const angle = -Math.PI / 2 + (index * 2 * Math.PI / values.length);
                const r = (Math.max(0, value) / maxValue) * radius;
                return { x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, angle, label: labels[index], value };
            });
            svg = `
                ${[0.33, 0.66, 1].map((scale) => `<circle cx="${cx}" cy="${cy}" r="${radius * scale}" class="info-chart-grid"></circle>`).join('')}
                ${points.map((point) => `<line x1="${cx}" y1="${cy}" x2="${cx + Math.cos(point.angle) * radius}" y2="${cy + Math.sin(point.angle) * radius}" class="info-chart-grid"></line>`).join('')}
                <polygon points="${points.map((point) => `${point.x},${point.y}`).join(' ')}" class="info-chart-radar-area"></polygon>
                ${points.map((point, index) => `
                    <circle cx="${point.x}" cy="${point.y}" r="4" fill="${colors[index % colors.length]}"></circle>
                    <text x="${cx + Math.cos(point.angle) * (radius + 24)}" y="${cy + Math.sin(point.angle) * (radius + 24)}" text-anchor="middle" class="info-chart-label">${esc(point.label)}</text>
                `).join('')}
            `;
        } else if (type === 'pie' || type === 'donut') {
            const total = values.reduce((sum, value) => sum + Math.max(0, value), 0) || 1;
            let start = -Math.PI / 2;
            const cx = 130;
            const cy = 135;
            const radius = 78;
            const slices = values.map((value, index) => {
                const amount = Math.max(0, value) / total;
                const end = start + amount * Math.PI * 2;
                const large = end - start > Math.PI ? 1 : 0;
                const x1 = cx + Math.cos(start) * radius;
                const y1 = cy + Math.sin(start) * radius;
                const x2 = cx + Math.cos(end) * radius;
                const y2 = cy + Math.sin(end) * radius;
                const path = `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2} Z`;
                start = end;
                return `<path d="${path}" fill="${colors[index % colors.length]}"></path>`;
            }).join('');
            svg = `
                ${slices}
                ${type === 'donut' ? `<circle cx="${cx}" cy="${cy}" r="42" class="info-chart-donut-hole"></circle>` : ''}
                ${labels.map((label, index) => `
                    <rect x="230" y="${70 + index * 24}" width="10" height="10" rx="2" fill="${colors[index % colors.length]}"></rect>
                    <text x="246" y="${79 + index * 24}" class="info-chart-label">${esc(label)} ${Math.round(values[index])}</text>
                `).join('')}
            `;
        } else {
            const barWidth = Math.max(18, 240 / labels.length - 8);
            svg = values.map((value, index) => {
                const barHeight = (Math.abs(value) / maxValue) * 142;
                const x = 46 + index * (270 / labels.length);
                const y = 205 - barHeight;
                return `
                    <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="5" fill="${colors[index % colors.length]}"></rect>
                    <text x="${x + barWidth / 2}" y="${y - 7}" text-anchor="middle" class="info-chart-value">${esc(String(Math.round(value)))}</text>
                    <text x="${x + barWidth / 2}" y="226" text-anchor="middle" class="info-chart-label">${esc(labels[index])}</text>
                `;
            }).join('') + `
                <line x1="36" y1="210" x2="332" y2="210" class="info-chart-axis"></line>
            `;
        }

        return `
            <div class="info-chart-wrap" data-chart-type="${escapeAttribute(type)}">
                <div class="info-chart-header">
                    <span>${esc(chart.title || 'Chart')}</span>
                    <span>${esc(type.replace('_', ' '))}</span>
                </div>
                <svg class="info-chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeAttribute(chart.title || 'Chart')}">${svg}</svg>
                ${chart.summary ? `<div class="info-chart-summary">${formatInlineBotText(chart.summary)}</div>` : ''}
            </div>
        `;
    };

    const renderPlainBotSegment = (segment, options = {}) => {
        const lines = String(segment || '').replace(/\r\n/g, '\n').split('\n');
        const blocks = [];
        let index = 0;
        let inSection = false;

        while (index < lines.length) {
            const line = lines[index].trim();
            if (!line) {
                index += 1;
                continue;
            }

            const heading = line.match(/^(#{1,4})\s+(.+)$/);
            if (heading) {
                const headingDepth = heading[1].length;
                if (options.isDeepSearch && headingDepth <= 3) {
                    if (inSection) {
                        blocks.push('</div>');
                    }
                    blocks.push('<div class="deep-search-section">');
                    inSection = true;
                }

                const tag = headingDepth <= 2 ? 'h3' : 'h4';
                const className = headingDepth <= 2 ? 'message-heading message-heading-title' : 'message-heading message-heading-section';
                blocks.push(`<${tag} class="${className}">${formatInlineBotText(heading[2], options)}</${tag}>`);
                index += 1;
                continue;
            }

            if (isTableRow(line) && lines[index + 1] && isTableSeparator(lines[index + 1])) {
                const rows = [];
                while (index < lines.length && isTableRow(lines[index].trim())) {
                    rows.push(lines[index].trim());
                    index += 1;
                }
                blocks.push(renderTable(rows, options));
                continue;
            }

            const unordered = line.match(/^[-*]\s+(.+)$/);
            const ordered = line.match(/^\d+[.)]\s+(.+)$/);
            if (unordered || ordered) {
                const tag = ordered ? 'ol' : 'ul';
                const items = [];
                while (index < lines.length) {
                    const itemLine = lines[index].trim();
                    const item = tag === 'ol'
                        ? itemLine.match(/^\d+[.)]\s+(.+)$/)
                        : itemLine.match(/^[-*]\s+(.+)$/);
                    if (!item) break;
                    items.push(`<li>${formatInlineBotText(item[1], options)}</li>`);
                    index += 1;
                }
                blocks.push(`<${tag}>${items.join('')}</${tag}>`);
                continue;
            }

            const paragraph = [line];
            index += 1;
            while (
                index < lines.length &&
                lines[index].trim() &&
                !/^#{1,4}\s+/.test(lines[index].trim()) &&
                !/^[-*]\s+/.test(lines[index].trim()) &&
                !/^\d+[.)]\s+/.test(lines[index].trim()) &&
                !(isTableRow(lines[index].trim()) && lines[index + 1] && isTableSeparator(lines[index + 1]))
            ) {
                paragraph.push(lines[index].trim());
                index += 1;
            }
            blocks.push(`<p>${formatInlineBotText(paragraph.join(' '), options)}</p>`);
        }

        if (inSection) {
            blocks.push('</div>');
        }

        return blocks.join('');
    };

    const parseWorkflowSteps = (text) => {
        const lines = String(text || '').split('\n');
        const steps = [];
        let metadata = {
            steps: 0,
            required_documents: 0,
            confidence: 'Low'
        };
        let currentStep = null;
        let beforeWorkflow = [];
        let afterWorkflow = [];
        let inWorkflow = false;
        let seenWorkflowHeading = false;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();

            if (/^(#{2,3})\s+Workflow\b/i.test(trimmed)) {
                seenWorkflowHeading = true;
                inWorkflow = true;
                continue;
            }

            if (!seenWorkflowHeading) {
                beforeWorkflow.push(line);
                continue;
            }

            if (inWorkflow) {
                if (/^(#{2,3})\s+(Key Requirements|Requirements|Forms|Links|Gaps|Follow-up|Sources)\b/i.test(trimmed)) {
                    inWorkflow = false;
                    afterWorkflow.push(line);
                    continue;
                }

                if (trimmed.startsWith('Steps:')) {
                    metadata.steps = parseInt(trimmed.replace('Steps:', '').trim(), 10) || 0;
                    continue;
                }
                if (trimmed.startsWith('Required Documents:')) {
                    metadata.required_documents = parseInt(trimmed.replace('Required Documents:', '').trim(), 10) || 0;
                    continue;
                }
                if (trimmed.startsWith('Confidence:')) {
                    metadata.confidence = trimmed.replace('Confidence:', '').trim();
                    continue;
                }
                if (trimmed.startsWith('Workflow Summary')) {
                    continue;
                }

                const stepMatch = trimmed.match(/^(\d+)[.)]\s+(.+)$/);
                if (stepMatch) {
                    const num = stepMatch[1];
                    const content = stepMatch[2];
                    const titleClean = content.replace(/^\*\*([^*]+)\*\*/, '$1').trim();
                    currentStep = {
                        number: num,
                        title: titleClean,
                        requirement: '',
                        dependency: '',
                        fee: '',
                        deadline: '',
                        branch: '',
                        source: '',
                        detail: ''
                    };
                    steps.push(currentStep);
                    continue;
                }

                if (currentStep && trimmed.startsWith('-')) {
                    const subtrimmed = trimmed.replace(/^-\s*/, '').trim();
                    const colonIdx = subtrimmed.indexOf(':');
                    if (colonIdx !== -1) {
                        const key = subtrimmed.slice(0, colonIdx).toLowerCase().trim();
                        const val = subtrimmed.slice(colonIdx + 1).trim();

                        if (key === 'requirement') {
                            currentStep.requirement = val;
                        } else if (key === 'dependency') {
                            currentStep.dependency = val;
                        } else if (key === 'fee') {
                            currentStep.fee = val;
                        } else if (key === 'deadline') {
                            currentStep.deadline = val;
                        } else if (key === 'branch') {
                            currentStep.branch = val;
                        } else if (key === 'source') {
                            currentStep.source = val;
                        } else if (key === 'detail' || key === 'details') {
                            currentStep.detail = val;
                        }
                    }
                    continue;
                }
            } else {
                afterWorkflow.push(line);
            }
        }

        return {
            before: beforeWorkflow.join('\n'),
            metadata,
            steps,
            after: afterWorkflow.join('\n')
        };
    };

    const renderInteractiveWorkflowContainerAndSteps = (parsed, options = {}) => {
        const linkifyOpts = { ...options, linkify: true };
        const metadata = parsed.metadata;
        const steps = parsed.steps;

        let html = `
            <div class="workflow-container">
                <div class="workflow-summary">
                    <div class="workflow-metadata">
                        <div class="workflow-metadata-item">
                            <span class="workflow-metadata-label">Steps</span>
                            <span class="workflow-metadata-value">${steps.length}</span>
                        </div>
                        <div class="workflow-metadata-item">
                            <span class="workflow-metadata-label">Required Docs</span>
                            <span class="workflow-metadata-value">${metadata.required_documents || 0}</span>
                        </div>
                        <div class="workflow-metadata-item">
                            <span class="workflow-metadata-label">Confidence</span>
                            <span class="workflow-metadata-value workflow-confidence-${(metadata.confidence || 'low').toLowerCase()}">${escapeHtml(metadata.confidence || 'Low')}</span>
                        </div>
                    </div>
                </div>
                
                <div class="workflow-steps">
        `;

        steps.forEach((step, index) => {
            const isCollapsed = index > 0;
            
            let sourceHtml = '';
            if (step.source) {
                const isUrl = /^(https?:\/\/|mailto:|tel:)/i.test(step.source);
                if (isUrl) {
                    sourceHtml = `<a class="workflow-step-source-link" href="${escapeAttribute(step.source)}" target="_blank" rel="noopener noreferrer" title="${escapeAttribute(step.source)}"><svg class="workflow-icon-link" viewBox="0 0 16 16" width="12" height="12"><path fill="currentColor" d="M7.775 3.275a.75.75 0 0 0-1.06 1.06l1.25 1.25a2 2 0 1 1-2.83 2.83l-2.5-2.5a2 2 0 0 1 0-2.83.75.75 0 0 0-1.06-1.06 3.5 3.5 0 0 0 0 4.95l2.5 2.5a3.5 3.5 0 0 0 4.95 0l1.25-1.25a.75.75 0 0 0 0-1.06zm-1.72 8a.75.75 0 0 0 1.06-1.06l-1.25-1.25a2 2 0 1 1 2.83-2.83l2.5 2.5a2 2 0 0 1 0 2.83.75.75 0 0 0 1.06 1.06 3.5 3.5 0 0 0 0-4.95l-2.5-2.5a3.5 3.5 0 0 0-4.95 0l-1.25 1.25a.75.75 0 0 0 0 1.06z"/></svg> Source</a>`;
                } else {
                    sourceHtml = `<span class="workflow-step-source-text"><svg class="workflow-icon-doc" viewBox="0 0 16 16" width="12" height="12"><path fill="currentColor" d="M4 1.75C4 .784 4.784 0 5.75 0h5.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0 1 14.25 16h-8.5A1.75 1.75 0 0 1 4 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25V5.5h-2.75A1.75 1.75 0 0 1 10 3.75V1.5Zm5 0v2.25c0 .138.112.25.25.25h2.25L10.75 1.5Z"/></svg> ${escapeHtml(step.source)}</span>`;
                }
            }

            html += `
                <div class="workflow-step-card ${isCollapsed ? 'collapsed' : ''}">
                    <div class="workflow-step-header" tabIndex="0" role="button" aria-expanded="${!isCollapsed}" onclick="this.parentElement.classList.toggle('collapsed'); this.setAttribute('aria-expanded', !this.parentElement.classList.contains('collapsed'));">
                        <div class="workflow-step-badge">${step.number}</div>
                        <div class="workflow-step-title">${formatInlineBotText(step.title, linkifyOpts)}</div>
                        <span class="workflow-step-chevron">
                            <svg viewBox="0 0 16 16" width="16" height="16"><path fill="currentColor" d="M4.47 5.22a.75.75 0 0 1 1.06 0L8 7.69l2.47-2.47a.75.75 0 0 1 1.06 1.06l-3 3a.75.75 0 0 1-1.06 0l-3-3a.75.75 0 0 1 0-1.06z"/></svg>
                        </span>
                    </div>
                    <div class="workflow-step-body">
                        <div class="workflow-step-body-content">
                            ${step.detail ? `<p class="workflow-step-detail-text">${formatInlineBotText(step.detail, linkifyOpts)}</p>` : ''}
                            <div class="workflow-badges-grid">
                                ${step.dependency ? `<div class="workflow-badge-row"><span class="workflow-badge-label workflow-badge-dependency">Dependency</span> <span class="workflow-badge-val">${formatInlineBotText(step.dependency, linkifyOpts)}</span></div>` : ''}
                                ${step.requirement ? `<div class="workflow-badge-row"><span class="workflow-badge-label workflow-badge-requirement">Requirement</span> <span class="workflow-badge-val">${formatInlineBotText(step.requirement, linkifyOpts)}</span></div>` : ''}
                                ${step.fee ? `<div class="workflow-badge-row"><span class="workflow-badge-label workflow-badge-fee">Fee</span> <span class="workflow-badge-val">${formatInlineBotText(step.fee, linkifyOpts)}</span></div>` : ''}
                                ${step.deadline ? `<div class="workflow-badge-row"><span class="workflow-badge-label workflow-badge-deadline">Deadline</span> <span class="workflow-badge-val">${formatInlineBotText(step.deadline, linkifyOpts)}</span></div>` : ''}
                                ${step.branch ? `<div class="workflow-badge-row"><span class="workflow-badge-label workflow-badge-branch">Branch</span> <span class="workflow-badge-val">${formatInlineBotText(step.branch, linkifyOpts)}</span></div>` : ''}
                                ${sourceHtml ? `<div class="workflow-badge-row"><span class="workflow-badge-label workflow-badge-source">Source</span> <span class="workflow-badge-val">${sourceHtml}</span></div>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    };

    const parseActionExecutionBlocks = (text = '') => {
        const actions = [];
        const allowedTypes = new Set(['fill', 'select', 'check', 'uncheck']);
        const pattern = /```action-execution\s*([\s\S]*?)```/gi;
        let cleaned = String(text || '');
        let match;
        while ((match = pattern.exec(text || '')) !== null) {
            try {
                const parsed = JSON.parse(match[1].trim());
                if (Array.isArray(parsed.actions)) {
                    actions.push(...parsed.actions.filter((action) => action && allowedTypes.has(String(action.type || '').toLowerCase())));
                }
                cleaned = cleaned.replace(match[0], '').trim();
            } catch (error) {
                console.warn('Invalid action-execution block:', error);
            }
        }
        return { cleaned, actions };
    };

    const confidenceClass = (confidence) => {
        const value = Number(confidence) || 0;
        if (value >= 0.9) return 'high';
        if (value >= 0.7) return 'medium';
        return 'low';
    };

    const AUTOFILL_LOW_CONFIDENCE_THRESHOLD = 0.7;
    const autofillSessionStorageKey = `web-chatbot-autofill-session:${window.location.origin}`;

    const isSensitiveAutofillTarget = (value = '') => /\b(password|passcode|pin|otp|one[-\s]?time|verification|security code|cvv|cvc|card number|credit card|debit card|bank|routing|account number|ssn|social security|tax id|passport|driver'?s license|license number|secret|token)\b/i.test(String(value || ''));

    const analyzeAutofillActionRisk = (action = {}) => {
        const confidence = Number(action.confidence || 0);
        const sensitive = isSensitiveAutofillTarget([
            action.field,
            action.label,
            action.placeholder,
            action.profile_key,
            action.type
        ].join(' '));
        return {
            confidence,
            confidenceKey: confidenceClass(confidence),
            lowConfidence: confidence > 0 && confidence < AUTOFILL_LOW_CONFIDENCE_THRESHOLD,
            sensitive,
            blocked: sensitive
        };
    };

    const summarizeAutofillRisk = (actions = []) => {
        const risks = actions.map(analyzeAutofillActionRisk);
        return {
            total: actions.length,
            sensitive: risks.filter((risk) => risk.sensitive).length,
            lowConfidence: risks.filter((risk) => risk.lowConfidence).length,
            blocked: risks.filter((risk) => risk.blocked).length,
            editable: actions.length
        };
    };

    const saveAutofillSession = (actions = [], phase = 'review') => {
        try {
            sessionStorage.setItem(autofillSessionStorageKey, JSON.stringify({
                url: window.location.href,
                origin: window.location.origin,
                title: document.title || '',
                phase,
                actions,
                updated_at: Date.now()
            }));
        } catch (error) {
            console.warn('Unable to save autofill session:', error);
        }
    };

    const loadAutofillSession = () => {
        try {
            const session = JSON.parse(sessionStorage.getItem(autofillSessionStorageKey) || 'null');
            if (!session || Date.now() - Number(session.updated_at || 0) > 60 * 60 * 1000) return null;
            return session;
        } catch (error) {
            return null;
        }
    };

    const appendActionConsentCard = (messageEl, actions = []) => {
        if (!messageEl || !actions.length) return;
        const card = document.createElement('div');
        card.className = 'action-consent-card';
        const riskSummary = summarizeAutofillRisk(actions);
        const rows = actions.map((action, index) => {
            const confidence = Number(action.confidence || 0);
            const confidenceLabel = confidence ? `${Math.round(confidence * 100)}%` : 'Review';
            const risk = analyzeAutofillActionRisk(action);
            const disabled = risk.blocked ? 'disabled' : '';
            const checked = risk.blocked || risk.lowConfidence ? '' : 'checked';
            const rowNote = risk.blocked
                ? 'Sensitive field blocked'
                : risk.lowConfidence
                ? 'Low confidence requires review'
                : 'Ready';
            return `
                <div class="action-row ${risk.blocked ? 'action-row-blocked' : ''} ${risk.lowConfidence ? 'action-row-low' : ''}" data-action-index="${index}">
                    <label class="action-include">
                        <input type="checkbox" class="action-include-input" ${checked} ${disabled}>
                        <span>${risk.blocked ? 'Blocked' : 'Use'}</span>
                    </label>
                    <label class="action-edit-field">
                        <span>Field</span>
                        <input class="action-field-input" value="${escapeAttribute(action.field || 'Field')}" ${disabled}>
                    </label>
                    <label class="action-edit-value">
                        <span>Value</span>
                        <input class="action-value-input" value="${escapeAttribute(action.type === 'check' ? 'true' : action.type === 'uncheck' ? 'false' : String(action.value ?? ''))}" ${disabled}>
                    </label>
                    <span class="action-confidence action-confidence-${risk.confidenceKey}">${confidenceLabel}</span>
                    <span class="action-row-note">${escapeHtml(rowNote)}</span>
                </div>
            `;
        }).join('');
        card.innerHTML = `
            <div class="action-card-header">
                <strong>Form Autofill Plan</strong>
                <span>${actions.length} action${actions.length === 1 ? '' : 's'}</span>
            </div>
            <div class="action-risk-summary">
                <strong>Privacy and Risk</strong>
                <span>${riskSummary.blocked} sensitive blocked</span>
                <span>${riskSummary.lowConfidence} low confidence</span>
                <span>Editable before approval</span>
            </div>
            <div class="action-table">${rows}</div>
            <p class="action-preview-note">Preview highlights matched fields without filling them. Low-confidence rows stay off until you review and enable them.</p>
            <details class="action-details">
                <summary>Details</summary>
                <pre>${escapeHtml(JSON.stringify({ actions }, null, 2))}</pre>
            </details>
            <div class="action-progress">
                <span class="action-status">Review the fields before filling.</span>
            </div>
            <div class="action-buttons">
                <button class="action-preview" type="button">Preview</button>
                <button class="action-approve" type="button">Approve Autofill</button>
                <button class="action-cancel" type="button">Cancel</button>
            </div>
        `;
        card.dataset.originalActions = JSON.stringify(actions);
        saveAutofillSession(actions, 'review');
        card.querySelector('.action-preview').onclick = () => previewAutofillPlan(card);
        card.querySelector('.action-approve').onclick = () => executeAutofillPlan(card);
        card.querySelector('.action-cancel').onclick = () => {
            card.classList.add('cancelled');
            card.querySelector('.action-status').textContent = 'Autofill cancelled.';
            card.querySelectorAll('button').forEach((button) => { button.disabled = true; });
        };
        messageEl.appendChild(card);
    };

    const formatBotMessage = (text, options = {}) => {
        const actionBlocks = parseActionExecutionBlocks(text);
        text = actionBlocks.cleaned;

        const rawJsonFlowchart = parseReactFlowJson(text);
        if (rawJsonFlowchart) {
            return renderReactFlowJsonFlowchart(text);
        }

        if ((text || '').includes('### Workflow')) {
            const parsed = parseWorkflowSteps(text);
            if (parsed.steps.length > 0) {
                const linkifyOpts = { ...options, linkify: true };
                const beforeHtml = parsed.before.trim() ? formatBotMessage(parsed.before, linkifyOpts) : '';
                const afterHtml = parsed.after.trim() ? formatBotMessage(parsed.after, linkifyOpts) : '';
                const workflowHtml = renderInteractiveWorkflowContainerAndSteps(parsed, linkifyOpts);
                return beforeHtml + workflowHtml + afterHtml;
            }
        }

        const parts = [];
        const codeBlockPattern = /```([^\n`]*)?\r?\n([\s\S]*?)```/g;
        let lastIndex = 0;
        let match;
        let renderedStructuredFlowchart = false;

        while ((match = codeBlockPattern.exec(text || '')) !== null) {
            if (match.index > lastIndex) {
                parts.push(renderPlainBotSegment(text.slice(lastIndex, match.index), options));
            }

            const languageName = (match[1] || '').trim().toLowerCase();
            const code = match[2].trim();
            const jsonFlowchart = languageName === 'json' ? parseReactFlowJson(code) : null;
            const infoChart = ['chart', 'json'].includes(languageName) ? parseChartJson(code) : null;
            if (jsonFlowchart) {
                parts.push(renderReactFlowJsonFlowchart(code));
                renderedStructuredFlowchart = true;
            } else if (infoChart) {
                parts.push(renderInfoChart(infoChart));
                renderedStructuredFlowchart = false;
            } else if (languageName === 'mermaid' || /^(graph|flowchart)\s+/i.test(code)) {
                if (!renderedStructuredFlowchart) {
                    parts.push(renderMermaidFlowchart(code));
                }
                renderedStructuredFlowchart = false;
            } else {
                const language = match[1] ? ` data-language="${escapeHtml(match[1])}"` : '';
                parts.push(`<pre class="message-code"${language}><code>${escapeHtml(code)}</code></pre>`);
                renderedStructuredFlowchart = false;
            }
            lastIndex = codeBlockPattern.lastIndex;
        }

        if (lastIndex < (text || '').length) {
            parts.push(renderPlainBotSegment(text.slice(lastIndex), options));
        }

        return parts.join('');
    };

    const closeFlowDiagramModal = () => {
        document.getElementById('web-chatbot-flow-modal')?.remove();
    };

    const closeTableModal = () => {
        document.getElementById('web-chatbot-table-modal')?.remove();
    };

    const openTableModal = (tableWrap) => {
        closeTableModal();
        // Use the full data source if the table was truncated in the chat message
        const sourceTable = tableWrap.querySelector('.full-table-source') || tableWrap.querySelector('table');
        if (!sourceTable) return;

        const clonedTable = sourceTable.cloneNode(true);
        const rowCount = clonedTable.querySelectorAll('tbody tr').length;
        const columnCount = clonedTable.querySelectorAll('thead th').length || clonedTable.querySelectorAll('tr:first-child > *').length;
        const isCompareTable = tableWrap.classList.contains('compare-result-table-wrap');

        const modal = document.createElement('div');
        modal.id = 'web-chatbot-table-modal';
        modal.className = `table-modal${isCompareTable ? ' table-modal-compare' : ''}`;
        modal.innerHTML = `
            <div class="table-modal-panel" role="dialog" aria-modal="true" aria-label="Table preview">
                <div class="table-modal-header">
                    <div>
                        <span>Data Table</span>
                        <small>${rowCount} rows${columnCount ? `, ${columnCount} columns` : ''}</small>
                    </div>
                    <button type="button" class="table-modal-close" aria-label="Close table preview">Close</button>
                </div>
                <div class="table-modal-body"></div>
            </div>
        `;
        modal.querySelector('.table-modal-body')?.appendChild(clonedTable);

        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.closest('.table-modal-close')) {
                closeTableModal();
            }
        });

        document.body.appendChild(modal);
        modal.querySelector('.table-modal-close')?.focus();
    };

    const currentFlowDiagramPalette = () => {
        const isDark = container.classList.contains('dark-mode');
        return isDark
            ? {
                bg: '#0b1220',
                subgraphBg: 'rgba(30, 41, 59, 0.68)',
                subgraphStroke: 'rgba(96, 165, 250, 0.36)',
                subgraphLabel: '#bfdbfe',
                nodeBg: '#172238',
                nodeStroke: '#60a5fa',
                nodeText: '#f8fafc',
                edge: '#22d3ee',
                glow: '#38bdf8',
                label: '#dbeafe'
            }
            : {
                bg: '#eef6ff',
                subgraphBg: 'rgba(219, 234, 254, 0.58)',
                subgraphStroke: 'rgba(37, 99, 235, 0.26)',
                subgraphLabel: '#1e3a8a',
                nodeBg: '#ffffff',
                nodeStroke: '#2563eb',
                nodeText: '#0f172a',
                edge: '#0e7490',
                glow: '#38bdf8',
                label: '#334155'
            };
    };

    const buildFlowDiagramSvgSource = (diagramWrap) => {
        const svg = diagramWrap?.querySelector('.flow-diagram-svg');
        if (!svg) return null;
        const palette = currentFlowDiagramPalette();

        const clone = svg.cloneNode(true);
        clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        const width = clone.viewBox?.baseVal?.width || svg.clientWidth || 900;
        const height = clone.viewBox?.baseVal?.height || svg.clientHeight || 520;
        clone.setAttribute('width', width);
        clone.setAttribute('height', height);

        const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
        style.textContent = `
            .flow-diagram-svg { background: ${palette.bg}; }
            .flow-diagram-subgraph-fill { fill: ${palette.subgraphBg}; stroke: ${palette.subgraphStroke}; stroke-width: 1.4; stroke-dasharray: 7 5; }
            .flow-diagram-subgraph-label { fill: ${palette.subgraphLabel}; font-family: Inter, Arial, sans-serif; font-size: 11px; font-weight: 850; letter-spacing: 0.03em; text-transform: uppercase; }
            .flow-diagram-node-shape { fill: ${palette.nodeBg}; stroke: ${palette.nodeStroke}; stroke-width: 1.7; }
            .flow-diagram-node text { fill: ${palette.nodeText}; font-family: Inter, Arial, sans-serif; font-size: 11.5px; font-weight: 750; }
            .flow-diagram-edge { fill: none; stroke: ${palette.edge}; stroke-width: 1.8; }
            .flow-diagram-edge-glow { fill: none; stroke: ${palette.glow}; stroke-width: 4.6; stroke-linecap: round; stroke-dasharray: 20 100; opacity: 0.58; }
            .flow-diagram-arrow { fill: ${palette.edge}; }
            .flow-diagram-edge-label { fill: ${palette.label}; stroke: ${palette.bg}; stroke-width: 4px; paint-order: stroke fill; font-family: Inter, Arial, sans-serif; font-size: 10px; font-weight: 800; }
        `;
        clone.insertBefore(style, clone.firstChild);

        return {
            source: new XMLSerializer().serializeToString(clone),
            width,
            height,
            background: palette.bg
        };
    };

    const downloadBlob = (blob, filename) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    const downloadFlowDiagram = (diagramWrap) => {
        const exportSvg = buildFlowDiagramSvgSource(diagramWrap);
        if (!exportSvg) return;

        downloadBlob(
            new Blob([exportSvg.source], { type: 'image/svg+xml;charset=utf-8' }),
            `flowchart-${new Date().toISOString().slice(0, 10)}.svg`
        );
    };

    const downloadFlowDiagramPng = async (diagramWrap) => {
        const exportSvg = buildFlowDiagramSvgSource(diagramWrap);
        if (!exportSvg) return;

        const svgBlob = new Blob([exportSvg.source], { type: 'image/svg+xml;charset=utf-8' });
        const svgUrl = URL.createObjectURL(svgBlob);
        const image = new Image();
        const scale = 2;

        try {
            await new Promise((resolve, reject) => {
                image.onload = resolve;
                image.onerror = () => reject(new Error('Could not render diagram image.'));
                image.src = svgUrl;
            });

            const canvas = document.createElement('canvas');
            canvas.width = Math.ceil(exportSvg.width * scale);
            canvas.height = Math.ceil(exportSvg.height * scale);
            const context = canvas.getContext('2d');
            if (!context) throw new Error('Canvas export is not available.');

            context.fillStyle = exportSvg.background;
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.drawImage(image, 0, 0, canvas.width, canvas.height);

            const pngBlob = await new Promise((resolve, reject) => {
                canvas.toBlob((blob) => {
                    if (blob) resolve(blob);
                    else reject(new Error('Could not create PNG file.'));
                }, 'image/png');
            });

            downloadBlob(pngBlob, `flowchart-${new Date().toISOString().slice(0, 10)}.png`);
        } catch (error) {
            console.error('Flow diagram PNG export failed:', error);
            addMessage(`PNG export failed: ${error.message}`, 'bot', { persist: false });
        } finally {
            URL.revokeObjectURL(svgUrl);
        }
    };

    const openFlowDiagramModal = (diagramWrap) => {
        const svg = diagramWrap?.querySelector('.flow-diagram-svg');
        if (!svg) return;

        closeFlowDiagramModal();
        const modal = document.createElement('div');
        modal.id = 'web-chatbot-flow-modal';
        modal.className = 'flow-diagram-modal';
        modal.innerHTML = `
            <div class="flow-diagram-modal-panel" role="dialog" aria-modal="true" aria-label="Flow diagram preview">
                <div class="flow-diagram-modal-header">
                    <span>Flow diagram</span>
                    <div class="flow-diagram-modal-tools" aria-label="Flow diagram view controls">
                        <button type="button" class="flow-diagram-zoom-out" title="Zoom out" aria-label="Zoom out">-</button>
                        <span class="flow-diagram-zoom-level" aria-live="polite">100%</span>
                        <button type="button" class="flow-diagram-zoom-in" title="Zoom in" aria-label="Zoom in">+</button>
                        <button type="button" class="flow-diagram-zoom-reset" title="Reset view" aria-label="Reset view">1:1</button>
                        <button type="button" class="flow-diagram-modal-close" aria-label="Close flow diagram">Close</button>
                    </div>
                </div>
                <div class="flow-diagram-modal-body">
                    <div class="flow-diagram-modal-viewport">
                        <div class="flow-diagram-modal-canvas">${svg.outerHTML}</div>
                    </div>
                </div>
            </div>
        `;
        const viewport = modal.querySelector('.flow-diagram-modal-viewport');
        const canvas = modal.querySelector('.flow-diagram-modal-canvas');
        const modalSvg = modal.querySelector('.flow-diagram-svg');
        const zoomLevel = modal.querySelector('.flow-diagram-zoom-level');
        const zoomIn = modal.querySelector('.flow-diagram-zoom-in');
        const zoomOut = modal.querySelector('.flow-diagram-zoom-out');
        const zoomReset = modal.querySelector('.flow-diagram-zoom-reset');
        const viewBox = svg.viewBox?.baseVal;
        const diagramWidth = viewBox?.width || svg.clientWidth || 900;
        const diagramHeight = viewBox?.height || svg.clientHeight || 520;
        const viewState = { scale: 1, x: 0, y: 0, dragging: false, startX: 0, startY: 0, originX: 0, originY: 0, pinchDistance: 0, pinchScale: 1 };
        const clampScale = (value) => Math.min(4, Math.max(0.35, value));
        const renderView = () => {
            canvas.style.transform = `translate(${viewState.x}px, ${viewState.y}px) scale(${viewState.scale})`;
            zoomLevel.textContent = `${Math.round(viewState.scale * 100)}%`;
        };
        const zoomAt = (nextScale, clientX, clientY) => {
            const previousScale = viewState.scale;
            const scale = clampScale(nextScale);
            if (scale === previousScale) return;
            const rect = viewport.getBoundingClientRect();
            const focalX = clientX - rect.left;
            const focalY = clientY - rect.top;
            viewState.x = focalX - ((focalX - viewState.x) * scale) / previousScale;
            viewState.y = focalY - ((focalY - viewState.y) * scale) / previousScale;
            viewState.scale = scale;
            renderView();
        };
        const resetView = () => {
            viewState.scale = 1;
            viewState.x = 0;
            viewState.y = 0;
            renderView();
        };
        const touchDistance = (touches) => {
            const dx = touches[0].clientX - touches[1].clientX;
            const dy = touches[0].clientY - touches[1].clientY;
            return Math.hypot(dx, dy);
        };
        const touchCenter = (touches) => ({
            x: (touches[0].clientX + touches[1].clientX) / 2,
            y: (touches[0].clientY + touches[1].clientY) / 2
        });

        if (modalSvg) {
            modalSvg.setAttribute('width', diagramWidth);
            modalSvg.setAttribute('height', diagramHeight);
        }
        renderView();
        zoomIn.onclick = () => zoomAt(viewState.scale * 1.2, viewport.getBoundingClientRect().left + viewport.clientWidth / 2, viewport.getBoundingClientRect().top + viewport.clientHeight / 2);
        zoomOut.onclick = () => zoomAt(viewState.scale / 1.2, viewport.getBoundingClientRect().left + viewport.clientWidth / 2, viewport.getBoundingClientRect().top + viewport.clientHeight / 2);
        zoomReset.onclick = resetView;
        viewport.addEventListener('wheel', (event) => {
            event.preventDefault();
            const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
            zoomAt(viewState.scale * factor, event.clientX, event.clientY);
        }, { passive: false });
        viewport.addEventListener('pointerdown', (event) => {
            if (event.button !== 0) return;
            viewState.dragging = true;
            viewState.startX = event.clientX;
            viewState.startY = event.clientY;
            viewState.originX = viewState.x;
            viewState.originY = viewState.y;
            viewport.classList.add('is-panning');
            viewport.setPointerCapture(event.pointerId);
        });
        viewport.addEventListener('pointermove', (event) => {
            if (!viewState.dragging) return;
            viewState.x = viewState.originX + event.clientX - viewState.startX;
            viewState.y = viewState.originY + event.clientY - viewState.startY;
            renderView();
        });
        const stopPan = (event) => {
            viewState.dragging = false;
            viewport.classList.remove('is-panning');
            if (event.pointerId !== undefined && viewport.hasPointerCapture(event.pointerId)) {
                viewport.releasePointerCapture(event.pointerId);
            }
        };
        viewport.addEventListener('pointerup', stopPan);
        viewport.addEventListener('pointercancel', stopPan);
        viewport.addEventListener('touchstart', (event) => {
            if (event.touches.length !== 2) return;
            event.preventDefault();
            viewState.pinchDistance = touchDistance(event.touches);
            viewState.pinchScale = viewState.scale;
        }, { passive: false });
        viewport.addEventListener('touchmove', (event) => {
            if (event.touches.length !== 2 || !viewState.pinchDistance) return;
            event.preventDefault();
            const center = touchCenter(event.touches);
            zoomAt(viewState.pinchScale * (touchDistance(event.touches) / viewState.pinchDistance), center.x, center.y);
        }, { passive: false });
        viewport.addEventListener('touchend', (event) => {
            if (event.touches && event.touches.length < 2) viewState.pinchDistance = 0;
        });
        modal.onclick = (event) => {
            if (event.target === modal || event.target.closest('.flow-diagram-modal-close')) {
                closeFlowDiagramModal();
            }
        };
        document.body.appendChild(modal);
    };

    const saveChatMessage = (text, sender, savedAt = Date.now()) => {
        const history = JSON.parse(localStorage.getItem(chatStorageKey) || '[]');
        history.push({ text, sender, savedAt });
        localStorage.setItem(chatStorageKey, JSON.stringify(history.slice(-30)));
    };

    const persistConversationMemory = () => {
        conversationMemory = {
            ...conversationMemory,
            turns: Array.isArray(conversationMemory.turns)
                ? conversationMemory.turns.slice(-MAX_MEMORY_TURNS)
                : [],
            updatedAt: Date.now()
        };
        sessionStorage.setItem(memoryKey, JSON.stringify(conversationMemory));
    };

    const sourceMemory = (sources = []) => sources.slice(0, 5).map((source) => ({
        id: source.id || '',
        url: source.url || '',
        title: source.title || source.url || '',
        source_type: source.source_type || ''
    }));

    const currentDocumentMemory = () => uploadedDocument ? {
        document_id: uploadedDocument.document_id || '',
        filename: uploadedDocument.filename || 'uploaded document',
        content_hash: uploadedDocument.content_hash || ''
    } : null;

    const rememberUserTurn = (question, mode = activeDocumentMode) => {
        const turn = {
            question,
            askedAt: Date.now(),
            page: {
                url: activeScopeUrl,
                visible_url: window.location.href,
                title: document.title || '',
                scope: activeScope
            },
            document_mode: mode,
            document: currentDocumentMemory(),
            compared_webpage: fetchedWebpageUrl ? { url: fetchedWebpageUrl } : null,
            answer: '',
            sources: []
        };

        const turns = Array.isArray(conversationMemory.turns) ? conversationMemory.turns : [];
        conversationMemory = { ...conversationMemory, turns: [...turns, turn].slice(-MAX_MEMORY_TURNS) };
        persistConversationMemory();
        return turn;
    };

    const rememberAssistantAnswer = (turn, answer, details = {}, sources = []) => {
        if (!turn) return;
        turn.answer = String(answer || '').slice(0, 900);
        turn.provider = details.provider || '';
        turn.model = details.model || '';
        turn.confidence = details.confidence || '';
        turn.sources = sourceMemory(sources);
        persistConversationMemory();
    };

    const conversationMemorySnapshot = (mode = activeDocumentMode) => ({
        current_page: {
            url: activeScopeUrl,
            visible_url: window.location.href,
            title: document.title || '',
            scope: activeScope
        },
        current_document: currentDocumentMemory(),
        current_document_mode: mode,
        fetched_webpage: fetchedWebpageUrl ? { url: fetchedWebpageUrl } : null,
        turns: Array.isArray(conversationMemory.turns)
            ? conversationMemory.turns
                .filter((turn) => turn && turn.document_mode === mode)
                .slice(-MAX_MEMORY_TURNS)
            : []
    });

    const modeScopedHistory = (mode = activeDocumentMode) => conversationHistory
        .filter((entry) => entry && entry.document_mode === mode)
        .slice(-8);

    const loadSettings = () => {
        const settings = JSON.parse(localStorage.getItem(settingsStorageKey) || '{}');
        if (settings.crawlLimit) crawlLimitInput.value = settings.crawlLimit;
        if (settings.modelChoice) modelSelect.value = settings.modelChoice;
        else if (settings.ollamaModel) modelSelect.value = `ollama:${settings.ollamaModel}`;
        if (settings.scopeChoice) scopeSelect.value = settings.scopeChoice;
        if (typeof settings.autoIndex === 'boolean') autoIndexInput.checked = settings.autoIndex;
        if (typeof settings.conciseAnswers === 'boolean') conciseInput.checked = settings.conciseAnswers;
    };

    const saveSettings = () => {
        localStorage.setItem(settingsStorageKey, JSON.stringify({
            crawlLimit: Number(crawlLimitInput.value) || 10,
            modelChoice: modelSelect.value || 'auto',
            scopeChoice: scopeSelect.value || 'page',
            autoIndex: autoIndexInput.checked,
            conciseAnswers: conciseInput.checked
        }));
    };

    const parseCustomProfileFields = (value = '') => {
        const fields = {};
        String(value || '').split(/\r?\n/).forEach((line) => {
            const match = line.match(/^\s*([^:=]+)\s*[:=]\s*(.+?)\s*$/);
            if (!match) return;
            const key = match[1].trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
            if (key) fields[key] = match[2].trim();
        });
        return fields;
    };

    const serializeCustomProfileFields = (fields = {}) => Object.entries(fields || {})
        .filter(([key, value]) => key && value)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n');

    const loadUserProfile = () => {
        let profile = {};
        try {
            profile = JSON.parse(localStorage.getItem(userProfileStorageKey) || '{}');
        } catch (error) {
            profile = {};
        }

        Object.entries(profileFields).forEach(([key, element]) => {
            if (element) element.value = profile[key] || '';
        });
        if (profileCustomFieldsInput) {
            profileCustomFieldsInput.value = serializeCustomProfileFields(profile.custom_fields || {});
        }
        return profile;
    };

    const saveUserProfile = () => {
        const profile = {};
        Object.entries(profileFields).forEach(([key, element]) => {
            profile[key] = (element?.value || '').trim();
        });
        profile.custom_fields = parseCustomProfileFields(profileCustomFieldsInput?.value || '');
        localStorage.setItem(userProfileStorageKey, JSON.stringify(profile));
        if (profileSaveStatus) {
            profileSaveStatus.textContent = 'Saved locally';
            window.clearTimeout(profileSaveStatus._clearTimer);
            profileSaveStatus._clearTimer = window.setTimeout(() => {
                profileSaveStatus.textContent = '';
            }, 1400);
        }
        return profile;
    };

    const currentUserProfile = () => {
        let profile = {};
        try {
            profile = JSON.parse(localStorage.getItem(userProfileStorageKey) || '{}');
        } catch (error) {
            profile = {};
        }
        return {
            full_name: profile.full_name || '',
            email: profile.email || '',
            phone: profile.phone || '',
            address: profile.address || '',
            city: profile.city || '',
            state: profile.state || '',
            country: profile.country || '',
            dob: profile.dob || '',
            linkedin: profile.linkedin || '',
            portfolio: profile.portfolio || '',
            ...(profile.custom_fields || {})
        };
    };

    const hasProfileValues = (profile = {}) => Object.values(profile).some((value) => String(value || '').trim());

    const setDocumentMode = (mode) => {
        activeDocumentMode = ['website', 'document', 'compare'].includes(mode) ? mode : 'website';
        sourceModeSelect.value = activeDocumentMode;
        if (modeSelect) modeSelect.value = activeDocumentMode;
        if (modeLabel) {
            const labels = { website: 'Website', document: 'Document', compare: 'Compare' };
            modeLabel.textContent = labels[activeDocumentMode] || labels.website;
        }
        if (modeCaption) {
            const captions = { website: 'Page chat', document: 'File chat', compare: 'File vs page' };
            modeCaption.textContent = captions[activeDocumentMode] || captions.website;
        }
        if (modeMark) {
            const marks = { website: 'W', document: 'D', compare: 'C' };
            modeMark.textContent = marks[activeDocumentMode] || marks.website;
            modeMark.dataset.mode = activeDocumentMode;
        }
        if (modeMenu) {
            modeMenu.querySelectorAll('.mode-picker-option').forEach((option) => {
                const selected = option.dataset.mode === activeDocumentMode;
                option.classList.toggle('active', selected);
                option.setAttribute('aria-selected', selected ? 'true' : 'false');
            });
        }

        // Sync toolbar tabs
        const modeTabsContainer = document.getElementById('cb-mode-tabs');
        if (modeTabsContainer) {
            modeTabsContainer.querySelectorAll('.cb-mode-tab').forEach(t => {
                t.classList.toggle('active', t.dataset.mode === activeDocumentMode);
            });
        }

        webpagePanel.classList.toggle('hidden', activeDocumentMode !== 'compare' || !compareAdvancedOpen);
        if (compareToolPanel) {
            compareToolPanel.classList.toggle('hidden', activeDocumentMode !== 'compare');
            updateCompareToolPanel();
        }

        if (activeDocumentMode === 'document' && uploadedDocument) {
            setFollowUps(['Summarize this document', 'List key points', 'Find risks or gaps']);
        } else if (activeDocumentMode === 'compare' && uploadedDocument) {
            setFollowUps(['Compare key points', 'Show differences', 'What is missing?']);
        } else if (activeDocumentMode === 'website') {
            setFollowUps(pageSpecificSuggestions([], 3));
        }
        updateDocumentChip();
    };

    const requestDocumentMode = (mode, { announce = false } = {}) => {
        setDocumentMode(mode);

        if (['document', 'compare'].includes(activeDocumentMode) && !uploadedDocument) {
            addMessage('Upload a document to start.', 'bot', { persist: false });
            fileInput.click();
        }

        if (!announce) return;
        const modeMessage = {
            website: 'Website mode active. Ask anything about this page.',
            document: 'Document mode active. Ask anything about your uploaded file.',
            compare: 'Compare mode active. Upload a document, then ask what is different from this webpage.'
        };
        addMessage(modeMessage[activeDocumentMode] || modeMessage.website, 'bot', { persist: false });
    };

    const updateDocumentChip = () => {
        if (!uploadedDocument) {
            documentChip.classList.add('hidden');
            documentChip.innerHTML = '';
            return;
        }
        const filename = uploadedDocument.filename || 'Document';
        const chars = uploadedDocument.text_chars || uploadedDocument.extracted_text?.length || 0;
        const size = chars > 1000 ? `${Math.round(chars / 1000)}k chars` : `${chars} chars`;
        documentChip.innerHTML = `
            <span class="document-chip-icon">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            </span>
            <span class="document-chip-name" title="${escapeHtml(filename)}">${escapeHtml(filename)}</span>
            <span class="document-chip-meta">${size}</span>
            <button class="document-mode-btn${activeDocumentMode === 'document' ? ' active' : ''}" data-document-mode="document" title="Ask questions about this document">Doc</button>
            <button class="document-mode-btn${activeDocumentMode === 'compare' ? ' active' : ''}" data-document-mode="compare" title="Compare document with webpage">Compare</button>
            <button data-remove-document title="Remove document" style="margin-left:2px;">&times;</button>
        `;
        documentChip.classList.remove('hidden');
    };

    const fileToBase64 = (file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const value = String(reader.result || '');
            resolve(value.includes(',') ? value.split(',').pop() : value);
        };
        reader.onerror = () => reject(reader.error || new Error('Unable to read file.'));
        reader.readAsDataURL(file);
    });

    const uploadDocument = async (file) => {
        if (!file) return;
        const status = addMessage(`Uploading ${file.name}...`, 'bot', { persist: false });
        status.classList.add('typing');
        try {
            const contentBase64 = await fileToBase64(file);
            updateStatusMessage(status, 'Processing document...');
            const result = await sendBackendMessage('fetchDocumentUpload', {
                filename: file.name,
                mime_type: file.type || '',
                page_url: window.location.href,
                content_base64: contentBase64
            });
            uploadedDocument = {
                ...result,
                extracted_text: result.extracted_text || ''
            };
            const modeAfterUpload = activeDocumentMode === 'compare' ? 'compare' : 'document';
            setDocumentMode(modeAfterUpload);
            updateDocumentChip();
            status.remove();
            addMessage(`Uploaded: **${result.filename}**`, 'bot', { persist: false });
            updateCompareToolPanel();
        } catch (error) {
            status.remove();
            addMessage('Document upload failed: ' + error.message, 'bot', { persist: false });
        } finally {
            fileInput.value = '';
        }
    };

    const appendModelOptions = (group, models, provider) => {
        const providerShort = provider === 'openrouter' ? 'OR' : provider === 'gemini' ? 'Gemini' : 'Ollama';
        const providerFull  = provider === 'openrouter' ? 'OpenRouter' : provider === 'gemini' ? 'Google Gemini' : 'Ollama';
        models.forEach((model) => {
            const option = document.createElement('option');
            option.value = `${provider}:${model}`;
            option.textContent = `${providerShort}: ${model.split('/').pop().replace(/:free$|:latest$/g, '')}`;
            option.title = `${providerFull} - ${model}`;
            group.appendChild(option);
        });
    };

    const fallbackModelOptions = () => ({
        openrouter_models: [
            'nvidia/nemotron-3-super-120b-a12b:free',
            'openai/gpt-oss-120b:free',
            'google/gemma-4-31b-it:free'
        ],
        gemini_models: [],
        ollama_models: ['qwen2.5:3b'],
        default_ollama_model: 'qwen2.5:3b'
    });

    const modelMeta = (value = 'auto', label = '') => {
        if (value.startsWith('openrouter:')) {
            const model = value.slice('openrouter:'.length);
            return {
                mark: 'OR',
                provider: 'OpenRouter',
                title: model.split('/').pop().replace(/:free$|:latest$/g, '') || 'OpenRouter',
                subtitle: model
            };
        }
        if (value.startsWith('gemini:')) {
            const model = value.slice('gemini:'.length);
            return {
                mark: 'GG',
                provider: 'Gemini',
                title: model.replace(/:free$|:latest$/g, '') || 'Gemini',
                subtitle: 'Google Gemini'
            };
        }
        if (value.startsWith('ollama:')) {
            const model = value.slice('ollama:'.length);
            return {
                mark: 'OL',
                provider: 'Ollama',
                title: model || 'Ollama',
                subtitle: 'Local model'
            };
        }
        return {
            mark: 'A',
            provider: 'Auto',
            title: label || 'Auto',
            subtitle: 'Best available'
        };
    };

    const syncModelPicker = () => {
        if (!modelLabel || !modelMark) return;
        const selected = modelSelect.options[modelSelect.selectedIndex];
        const meta = modelMeta(modelSelect.value, selected?.textContent || 'Auto');
        modelLabel.textContent = meta.provider;
        modelMark.textContent = meta.mark;
        modelMark.dataset.provider = meta.provider.toLowerCase();

        if (modelMenu) {
            modelMenu.querySelectorAll('.model-picker-option').forEach((option) => {
                const selectedOption = option.dataset.value === modelSelect.value;
                option.classList.toggle('active', selectedOption);
                option.setAttribute('aria-selected', selectedOption ? 'true' : 'false');
            });
        }
    };

    const rebuildModelPicker = () => {
        if (!modelMenu) return;
        modelMenu.innerHTML = '';

        // Walk the native select's children — mix of <optgroup> and <option>
        Array.from(modelSelect.children).forEach((child) => {
            if (child.tagName === 'OPTGROUP') {
                // Group header label
                const groupLabel = document.createElement('div');
                groupLabel.className = 'model-picker-group-label';
                groupLabel.textContent = child.label;
                modelMenu.appendChild(groupLabel);

                // Options inside the group
                Array.from(child.children).forEach((option) => {
                    const meta = modelMeta(option.value, option.textContent);
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'model-picker-option';
                    btn.setAttribute('role', 'option');
                    btn.dataset.value = option.value;
                    btn.innerHTML = `
                        <span class="model-option-mark" data-provider="${escapeAttribute(meta.provider.toLowerCase())}" aria-hidden="true">${escapeHtml(meta.mark)}</span>
                        <span class="model-option-copy">
                            <span class="model-option-title">${escapeHtml(meta.title)}</span>
                            <span class="model-option-subtitle">${escapeHtml(meta.subtitle)}</span>
                        </span>
                    `;
                    modelMenu.appendChild(btn);
                });
            } else if (child.tagName === 'OPTION') {
                // Top-level option (e.g. Auto)
                const meta = modelMeta(child.value, child.textContent);
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'model-picker-option';
                btn.setAttribute('role', 'option');
                btn.dataset.value = child.value;
                btn.innerHTML = `
                    <span class="model-option-mark" data-provider="${escapeAttribute(meta.provider.toLowerCase())}" aria-hidden="true">${escapeHtml(meta.mark)}</span>
                    <span class="model-option-copy">
                        <span class="model-option-title">${escapeHtml(meta.title)}</span>
                        <span class="model-option-subtitle">${escapeHtml(meta.subtitle)}</span>
                    </span>
                `;
                modelMenu.appendChild(btn);
            }
        });

        syncModelPicker();
    };

    const loadModelOptions = async () => {
        let result = fallbackModelOptions();
        try {
            const settings = JSON.parse(localStorage.getItem(settingsStorageKey) || '{}');
            const preferredChoice = settings.modelChoice || modelSelect.value || 'auto';
            result = { ...result, ...(await sendBackendMessage('fetchOllamaModels', {})) };
            const openrouterModels = Array.isArray(result.openrouter_models) ? result.openrouter_models : [];
            const ollamaModels = Array.isArray(result.ollama_models) && result.ollama_models.length
                ? result.ollama_models
                : (Array.isArray(result.models) && result.models.length ? result.models : [result.default_ollama_model || result.default_model || 'qwen2.5:3b']);

            modelSelect.innerHTML = '';
            const autoOption = document.createElement('option');
            autoOption.value = 'auto';
            autoOption.textContent = 'Auto';
            autoOption.title = 'Auto - OpenRouter first, Gemini second, Ollama fallback';
            modelSelect.appendChild(autoOption);

            if (openrouterModels.length) {
                const openrouterGroup = document.createElement('optgroup');
                openrouterGroup.label = 'OpenRouter';
                appendModelOptions(openrouterGroup, openrouterModels, 'openrouter');
                modelSelect.appendChild(openrouterGroup);
            }

            const geminiModels = result.gemini_models || [];
            if (geminiModels.length) {
                const geminiGroup = document.createElement('optgroup');
                geminiGroup.label = 'Gemini (Google)';
                appendModelOptions(geminiGroup, geminiModels, 'gemini');
                modelSelect.appendChild(geminiGroup);
            }

            if (ollamaModels.length) {
                const ollamaGroup = document.createElement('optgroup');
                ollamaGroup.label = 'Ollama';
                appendModelOptions(ollamaGroup, ollamaModels, 'ollama');
                modelSelect.appendChild(ollamaGroup);
            }

            const availableValues = Array.from(modelSelect.options).map((option) => option.value);
            modelSelect.value = availableValues.includes(preferredChoice) ? preferredChoice : 'auto';
            rebuildModelPicker();
            saveSettings();
        } catch (error) {
            console.warn('Unable to load model options:', error);
            const settings = JSON.parse(localStorage.getItem(settingsStorageKey) || '{}');
            const preferredChoice = settings.modelChoice || modelSelect.value || 'auto';
            modelSelect.innerHTML = '';
            const autoOption = document.createElement('option');
            autoOption.value = 'auto';
            autoOption.textContent = 'Auto';
            autoOption.title = 'Auto - OpenRouter first, Gemini second, Ollama fallback';
            modelSelect.appendChild(autoOption);

            const openrouterGroup = document.createElement('optgroup');
            openrouterGroup.label = 'OpenRouter';
            appendModelOptions(openrouterGroup, result.openrouter_models, 'openrouter');
            modelSelect.appendChild(openrouterGroup);

            const ollamaGroup = document.createElement('optgroup');
            ollamaGroup.label = 'Ollama';
            appendModelOptions(ollamaGroup, result.ollama_models, 'ollama');
            modelSelect.appendChild(ollamaGroup);

            const availableValues = Array.from(modelSelect.options).map((option) => option.value);
            modelSelect.value = availableValues.includes(preferredChoice) ? preferredChoice : 'auto';
            rebuildModelPicker();
        }
    };

    const selectedModelRequest = () => {
        const choice = modelSelect.value || 'auto';
        if (choice.startsWith('openrouter:')) {
            return {
                force_provider: 'openrouter',
                openrouter_model: choice.slice('openrouter:'.length),
                ollama_model: ''
            };
        }
        if (choice.startsWith('ollama:')) {
            return {
                force_provider: 'ollama',
                openrouter_model: '',
                ollama_model: choice.slice('ollama:'.length)
            };
        }
        if (choice.startsWith('gemini:')) {
            return {
                force_provider: 'gemini',
                openrouter_model: '',
                ollama_model: '',
                gemini_model: choice.slice('gemini:'.length)
            };
        }
        return {
            force_provider: '',
            openrouter_model: '',
            ollama_model: '',
            gemini_model: ''
        };
    };

    const setBackendStatus = (online, text) => {
        statusDot.classList.toggle('offline', !online);
        statusDot.classList.toggle('online', online);
        statusText.textContent = text;
    };

    const setIndexStatus = (text) => {
        if (statusDot.classList.contains('online')) {
            statusText.textContent = text;
        }
    };

    const inputPlaceholders = [
        'What is on your mind?',
        'Ask about this page...',
        'What should I explain?',
        'Need a quick summary?',
        'Ask anything here...',
        'Compare or question it...'
    ];

    const typeInputPlaceholder = (text, charIndex = 0) => {
        if (!input || input.value.trim()) {
            placeholderTimer = window.setTimeout(startPlaceholderRotation, 800);
            return;
        }

        input.placeholder = text.slice(0, charIndex);
        if (charIndex <= text.length) {
            placeholderTimer = window.setTimeout(() => typeInputPlaceholder(text, charIndex + 1), 42);
            return;
        }

        placeholderTimer = window.setTimeout(startPlaceholderRotation, 1600);
    };

    const startPlaceholderRotation = () => {
        if (!input || input.value.trim()) return;
        if (placeholderTimer) window.clearTimeout(placeholderTimer);
        const nextPlaceholder = inputPlaceholders[placeholderIndex % inputPlaceholders.length];
        placeholderIndex += 1;
        typeInputPlaceholder(nextPlaceholder);
    };

    const checkBackendHealth = async () => {
        try {
            await sendBackendMessage('fetchHealth', {});
            setBackendStatus(true, 'System Ready');
        } catch (error) {
            setBackendStatus(false, 'System Offline');
        }
    };

    const copyTextToClipboard = async (text) => {
        const value = String(text || '');
        if (!value) return false;

        try {
            await navigator.clipboard.writeText(value);
            return true;
        } catch (error) {
            const textarea = document.createElement('textarea');
            textarea.value = value;
            textarea.setAttribute('readonly', '');
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            const copied = document.execCommand('copy');
            textarea.remove();
            return copied;
        }
    };

    const appendCopyButton = (messageEl, text) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'message-copy-button';
        button.title = 'Copy message';
        button.setAttribute('aria-label', 'Copy message');
        button.innerHTML = `
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        `;

        button.onclick = async (event) => {
            event.stopPropagation();
            const copied = await copyTextToClipboard(text);
            if (!copied) return;

            button.classList.add('copied');
            button.title = 'Copied';
            button.setAttribute('aria-label', 'Copied');
            button.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            `;
            window.setTimeout(() => {
                button.classList.remove('copied');
                button.title = 'Copy message';
                button.setAttribute('aria-label', 'Copy message');
                button.innerHTML = `
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                `;
            }, 1200);
        };

        messageEl.appendChild(button);
    };

    const formatMessageTime = (value = Date.now()) => {
        const date = value instanceof Date ? value : new Date(value);
        const safeDate = Number.isNaN(date.getTime()) ? new Date() : date;
        return safeDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const appendMessageTimestamp = (messageEl, value = Date.now()) => {
        if (!messageEl || messageEl.classList.contains('tool-status-message')) return;
        const existing = Array.from(messageEl.children).find((child) => child.classList.contains('message-time'));
        const timeEl = existing || document.createElement('div');
        timeEl.className = 'message-time';
        timeEl.textContent = formatMessageTime(value);
        if (!existing) messageEl.appendChild(timeEl);
    };

    const userAskedForLinks = (question = '') => /\b(link|links|url|urls|source|sources|reference|references|contact|email|phone|open|navigate|go to|visit|website)\b/i.test(question);

    const detectAutofillIntent = (question = '') =>
        /\b(auto[\s-]?fill|autofill|fill\s+(this\s+)?(form|application|fields?)|fill\s+(it|them)\s+out|fill\s+out\s+(the|this)\s+(form|application|fields?)|fill\s+the\s+form|complete\s+(this\s+)?(application|form|fields?)|populate\s+(the\s+)?(fields?|form|inputs?)|fill\s+in\s+(the|this)\s+(form|application|fields?)|can\s+you\s+fill|fill\s+(this|the)\s+out)\b/i
        .test(question);

    // ── Hybrid Intent Router — frontend helper ────────────────────────────────
    // Calls /intent-route for queries that are not obviously a chart, flowchart,
    // autofill, or workflow (those are handled by fast local checks first).
    // Returns the server intent-route response object.
    const callIntentRouter = async (question, options = {}) => {
        try {
            const inputs = scrapePageInputs ? scrapePageInputs() : [];
            const profile = currentUserProfile ? currentUserProfile() : null;
            const modelRequest = selectedModelRequest ? selectedModelRequest() : {};
            return await sendBackendMessage('fetchIntentRoute', {
                question,
                page_has_form: inputs.length > 0,
                visible_inputs: inputs.length,
                profile_exists: !!(profile && hasProfileValues && hasProfileValues(profile)),
                workflow_keywords_present: /\b(admission|application|enroll|eligib|steps?|process|deadline|requirements?)\b/i.test(question),
                action_keywords_present: /\b(click|open|navigate|scroll|go\s+to|press|select)\b/i.test(question),
                current_mode: options.mode || 'website',
                page_title: document.title || '',
                page_summary: '',
                ollama_model: modelRequest.ollama_model || '',
                openrouter_model: modelRequest.openrouter_model || '',
                gemini_model: modelRequest.gemini_model || '',
                force_provider: options.forceProvider || modelRequest.force_provider || '',
                // Use regex-only (skip_llm) for speed; LLM fallback only when
                // the user explicitly triggers the router via /intent-route.
                skip_llm: true,
            });
        } catch (err) {
            console.warn('[IntentRouter] callIntentRouter error:', err);
            return { intent: 'normal_chat', confidence: 0.5, router: 'fallback',
                     needs_clarification: false, clarification_prompt: '', safety: { ok: true } };
        }
    };
    // ─────────────────────────────────────────────────────────────────────────

    const isMessagesNearBottom = () => {
        if (!messagesContainer) return true;
        return messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 56;
    };

    const updateScrollDownButton = () => {
        if (!scrollDownBtn) return;
        scrollDownBtn.classList.toggle('hidden', isMessagesNearBottom());
    };

    const scrollMessagesToBottom = (smooth = false) => {
        if (!messagesContainer) return;
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: smooth ? 'smooth' : 'auto'
        });
        window.setTimeout(updateScrollDownButton, smooth ? 220 : 0);
    };

    const addMessage = (text, sender, options = {}) => {
        const shouldPersist = options.persist !== false;
        const sentAt = options.timestamp || options.savedAt || Date.now();
        const msg = document.createElement('div');
        const isDeepSearch = Boolean(options.isDeepSearch);
        msg.className = `message ${sender} ${isDeepSearch ? 'message-deep-search' : 'message-quick-search'}`;
        const actionBlocks = sender === 'bot' ? parseActionExecutionBlocks(text) : { cleaned: text, actions: [] };
        
        if (sender === 'bot') {
            const contentHtml = formatBotMessage(text, { linkify: options.allowLinks === true });
            if (isDeepSearch) {
                let headerHtml = `
                    <div class="deep-search-header">
                        <span class="icon">🧠</span>
                        <span class="title">Aletheia Research Report</span>
                    </div>
                `;
                
                if (options.deepSearchSummary) {
                    const sum = options.deepSearchSummary;
                    let covHtml = '';
                    if (sum.coverage) {
                        covHtml = `
                            <div class="deep-search-coverage">
                                <h4>Research Coverage</h4>
                                <div class="coverage-grid">
                                    ${Object.entries(sum.coverage).map(([k, v]) => `<div class="coverage-item ${v ? 'found' : 'missing'}"><span class="icon">${v ? '✓' : '✗'}</span> <span class="label">${k.charAt(0).toUpperCase() + k.slice(1)}</span></div>`).join('')}
                                </div>
                            </div>
                        `;
                    }
                    let missHtml = '';
                    if (sum.missing_information && sum.missing_information.length > 0) {
                        missHtml = `
                            <div class="deep-search-missing-info">
                                <h4>Information Not Found</h4>
                                <ul>
                                    ${sum.missing_information.map(info => `<li>${info}</li>`).join('')}
                                </ul>
                            </div>
                        `;
                    }
                    
                    headerHtml += `
                        <div class="deep-search-summary">
                            <div class="stat"><span>Pages Crawled:</span> <strong>${sum.pages_crawled || 0}</strong></div>
                            <div class="stat"><span>Sources Used:</span> <strong>${sum.sources_used || 0}</strong></div>
                            <div class="stat"><span>Confidence:</span> <strong>${sum.confidence || 'N/A'}</strong></div>
                        </div>
                        ${covHtml}
                        ${missHtml}
                    `;
                }
                msg.innerHTML = headerHtml + `<div class="message-body">${contentHtml}</div>`;
            } else {
                msg.innerHTML = `<div class="message-body">${contentHtml}</div>`;
            }
            appendActionConsentCard(msg, actionBlocks.actions);
            if (options.allowLinks) {
                appendOpenLinkButtons(msg, text);
            }
        } else {
            msg.innerText = text;
        }
        appendCopyButton(msg, text);
        appendMessageTimestamp(msg, sentAt);
        messagesContainer.appendChild(msg);
        scrollMessagesToBottom();

        if (shouldPersist) {
            saveChatMessage(text, sender, sentAt);
        }

        // Track in adaptive conversation history
        if (shouldPersist) {
            conversationHistory.push({
                sender,
                text: text.slice(0, 400),
                document_mode: activeDocumentMode
            });
            if (conversationHistory.length > MAX_HISTORY) {
                conversationHistory = conversationHistory.slice(-MAX_HISTORY);
            }
            sessionStorage.setItem(historyKey, JSON.stringify(conversationHistory));
        }

        return msg;
    };

    const loadChatHistory = () => {
        const history = JSON.parse(localStorage.getItem(chatStorageKey) || '[]');
        history.forEach((entry) => {
            if (entry && entry.text && entry.sender) {
                addMessage(entry.text, entry.sender, { persist: false, timestamp: entry.savedAt });
            }
        });
    };

    const extractUrls = (text) => {
        const matches = text.match(/https?:\/\/[^\s)]+|mailto:[^\s)]+|tel:[^\s)]+/g) || [];
        return [...new Set(matches.map((url) => url.replace(/[.,;]+$/, '')))];
    };

    const appendOpenLinkButtons = (messageEl, text) => {
        const urls = extractUrls(text).slice(0, 3);
        if (!urls.length) return;

        const actions = document.createElement('div');
        actions.className = 'message-link-actions';

        urls.forEach((url, index) => {
            const link = document.createElement('button');
            link.type = 'button';
            link.title = url;
            link.innerHTML = `
                <span class="link-label">${urls.length === 1 ? 'Open link' : `Link ${index + 1}`}</span>
                <span class="link-url">${escapeHtml(shortDisplayUrl(url))}</span>
            `;
            link.onclick = () => {
                addHumanReviewCard({
                    intent: { type: 'open', target: shortDisplayUrl(url) },
                    match: { label: shortDisplayUrl(url), url },
                    onApprove: () => {
                        addMessage(`Opening ${shortDisplayUrl(url)}...`, 'bot', { persist: false });
                        if (/^(mailto:|tel:)/i.test(url)) {
                            window.location.href = url;
                            return;
                        }
                        window.open(url, '_blank', 'noopener,noreferrer');
                    }
                });
            };
            actions.appendChild(link);
        });

        messageEl.appendChild(actions);
    };

    const appendSourceCards = (messageEl, sources = []) => {
        if (!sources.length) return;

        const sourceWrap = document.createElement('div');
        sourceWrap.className = 'source-preview-container';

        sources.slice(0, 4).forEach((source) => {
            const isDoc = source.source_type === 'document' || String(source.url || '').startsWith('document://');
            const relevanceLabel = source.relevance_score ? (source.relevance_score >= 0.85 ? 'High' : 'Medium') : 'High';
            const lastUpdated = source.last_updated || 'June 2026';
            const title = source.title && source.title !== source.url ? source.title : (isDoc ? 'Uploaded document' : 'Web Source');
            const section = source.section || 'General';
            const snippet = source.snippet || 'Relevant match from site crawl and deep database retrieval.';

            const previewCard = document.createElement('a');
            previewCard.className = 'source-preview-card';
            if (isDoc) {
                previewCard.removeAttribute('href'); // no link for local docs
                previewCard.style.cursor = 'default';
            } else {
                previewCard.href = source.url;
                previewCard.target = '_blank';
                previewCard.rel = 'noopener noreferrer';
            }

            previewCard.innerHTML = `
                <div class="source-preview-header">
                    <span class="source-preview-title">${escapeHtml(source.id ? `[${source.id}] ${title}` : title)}</span>
                    <span class="source-preview-relevance">${escapeHtml(relevanceLabel)} Relevance</span>
                </div>
                <div class="source-preview-meta">Section: ${escapeHtml(section)} &bull; Updated: ${escapeHtml(lastUpdated)}</div>
                <div class="source-preview-snippet">${escapeHtml(snippet)}</div>
            `;
            sourceWrap.appendChild(previewCard);
        });

        messageEl.appendChild(sourceWrap);
    };

    const appendModelBadge = (messageEl, details = {}) => {
        const provider = details.provider || 'AI';
        const model = details.model || '';
        const confidence = details.confidence || '';
        const badge = document.createElement('div');
        badge.className = `model-badge ${confidence === 'low' ? 'low-confidence' : ''}`;
        badge.textContent = model ? `${provider}: ${model}` : provider;
        if (confidence && confidence !== 'high') {
            badge.textContent += ` - ${confidence} confidence`;
        }
        messageEl.prepend(badge);
    };

    const appendFeedback = (messageEl, feedbackPayload = {}) => {
        const feedback = document.createElement('div');
        feedback.className = 'message-feedback';
        feedback.innerHTML = '<button title="Helpful">👍</button><button title="Not helpful">👎</button>';
        feedback.onclick = (event) => {
            const button = event.target.closest('button');
            if (!button) return;
            feedback.querySelectorAll('button').forEach((item) => item.classList.remove('selected'));
            button.classList.add('selected');
        };
        messageEl.appendChild(feedback);
    };

    const appendFunctionalFeedback = (messageEl, feedbackPayload = {}) => {
        const feedback = document.createElement('div');
        feedback.className = 'message-feedback';
        feedback.innerHTML = '<button title="Helpful" data-rating="up">Helpful</button><button title="Not helpful" data-rating="down">Improve</button>';
        feedback.onclick = async (event) => {
            const button = event.target.closest('button');
            if (!button) return;
            const rating = button.dataset.rating;
            feedback.querySelectorAll('button').forEach((item) => item.classList.remove('selected'));
            button.classList.add('selected');
            feedback.classList.add('submitted');

            try {
                await sendBackendMessage('fetchFeedback', {
                    ...feedbackPayload,
                    rating
                });
                if (rating === 'down') {
                    feedback.innerHTML = '<span>Improving...</span>';
                    handleSend(feedbackPayload.question || 'Improve the previous answer', {
                        skipUserEcho: true,
                        contentHash: feedbackPayload.contentHash || '',
                        revisionOf: {
                            question: feedbackPayload.question || '',
                            answer: feedbackPayload.answer || '',
                            reason: 'Improve button clicked'
                        }
                    });
                    return;
                }
                feedback.innerHTML = '<span>Feedback saved</span>';
            } catch (error) {
                feedback.classList.remove('submitted');
                button.textContent = 'Retry';
                console.warn('Feedback failed:', error);
            }
        };
        messageEl.appendChild(feedback);
    };

    const attachFlowDiagramQuestions = (messageEl, question) => {
        const originalQuestion = String(question || '').trim();
        if (!messageEl || !originalQuestion) return;
        messageEl.querySelectorAll('.flow-diagram-wrap').forEach((diagram) => {
            diagram.dataset.originalQuestion = originalQuestion;
        });
    };

    const clearFollowUpButtons = () => {
        messagesContainer.querySelectorAll('.message-followups').forEach((item) => item.remove());
    };

    const appendFollowUpButtons = (messageEl, items = []) => {
        const questions = items.filter(Boolean).slice(0, 3);
        if (!questions.length) return;

        const followUps = document.createElement('div');
        followUps.className = 'message-followups';
        questions.forEach((question) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = question;
            button.onclick = () => {
                clearFollowUpButtons();
                handleSend(question);
            };
            followUps.appendChild(button);
        });
        messageEl.insertAdjacentElement('afterend', followUps);
    };

    const setFollowUps = () => {
        // Follow-up prompts live as separate action rows under bot messages.
    };

    const addBotMessageAnimated = async (text, sources = [], usedExternalSearch = false, details = {}) => {
        const msg = document.createElement('div');
        msg.className = 'message bot';
        messagesContainer.appendChild(msg);
        const shouldShowLinks = userAskedForLinks(details.question || '');
        const actionBlocks = parseActionExecutionBlocks(text);
        const displayText = actionBlocks.cleaned || 'Review the autofill plan below.';

        const step = Math.max(4, Math.ceil(displayText.length / 80));
        for (let index = step; index < displayText.length; index += step) {
            msg.innerHTML = formatBotMessage(displayText.slice(0, index), { linkify: shouldShowLinks });
            scrollMessagesToBottom();
            await new Promise((resolve) => setTimeout(resolve, 15));
        }

        msg.innerHTML = formatBotMessage(displayText, { linkify: shouldShowLinks });
        appendActionConsentCard(msg, actionBlocks.actions);
        attachFlowDiagramQuestions(msg, details.question || '');
        appendModelBadge(msg, details);
        
        if (usedExternalSearch) {
            const badge = document.createElement('div');
            badge.className = 'external-search-indicator';
            badge.textContent = 'External Search Used';
            msg.prepend(badge);
        }

        if (shouldShowLinks) {
            appendOpenLinkButtons(msg, text);
        }
        if (shouldShowLinks) {
            appendSourceCards(msg, sources);
        }
        appendCopyButton(msg, text);
        appendFunctionalFeedback(msg, {
            url: activeScopeUrl,
            question: details.question || '',
            answer: text,
            provider: details.provider || '',
            model: details.model || '',
            sources,
            contentHash: details.contentHash || ''
        });
        appendFollowUpButtons(msg, details.followUps || []);
        const deliveredAt = Date.now();
        appendMessageTimestamp(msg, deliveredAt);
        scrollMessagesToBottom();
        saveChatMessage(text, 'bot', deliveredAt);
        rememberAssistantAnswer(details.memoryTurn, text, details, sources);
        window.setTimeout(() => autoHighlightAnswerMatch(details.question || '', text), 120);
        return msg;
    };

    const createStreamingBotMessage = (detail = 'Preparing response...', options = {}) => {
        const msg = document.createElement('div');
        const isDeepSearch = Boolean(options.isDeepSearch);
        msg.className = `message bot streaming ${isDeepSearch ? 'message-deep-search' : 'message-quick-search'}`;
        let innerHtml = '';
        if (isDeepSearch) {
            innerHtml += `
                <div class="deep-search-header">
                    <span class="icon">🧠</span>
                    <span class="title">Aletheia Research Report</span>
                </div>
            `;
        }
        innerHtml += `
            <div class="processing-status-widget" role="status" aria-live="polite">
                <div class="psw-header">
                    <span class="psw-title">Processing Request</span>
                    <span class="psw-loader"></span>
                </div>
                <div class="psw-steps">
                    <div class="psw-step step-retrieval active">
                        <span class="psw-step-bullet"></span>
                        <span class="psw-step-text">Searching database and local page cache...</span>
                    </div>
                    <div class="psw-step step-web">
                        <span class="psw-step-bullet"></span>
                        <span class="psw-step-text">Fetching external web results if needed...</span>
                    </div>
                    <div class="psw-step step-rerank">
                        <span class="psw-step-bullet"></span>
                        <span class="psw-step-text">Ranking matching sections and validation...</span>
                    </div>
                    <div class="psw-step step-generation">
                        <span class="psw-step-bullet"></span>
                        <span class="psw-step-text">Drafting final answer using LLM...</span>
                    </div>
                </div>
            </div>
        `;
        msg.innerHTML = innerHtml;
        messagesContainer.appendChild(msg);
        scrollMessagesToBottom();

        // Simulate step transitions based on standard retrieval timing:
        // Step 1 -> Step 2
        setTimeout(() => {
            const step1 = msg.querySelector('.step-retrieval');
            const step2 = msg.querySelector('.step-web');
            if (step1 && step2 && !msg.classList.contains('done-generating')) {
                step1.classList.remove('active');
                step1.classList.add('complete');
                step2.classList.add('active');
            }
        }, 550);

        // Step 2 -> Step 3
        setTimeout(() => {
            const step2 = msg.querySelector('.step-web');
            const step3 = msg.querySelector('.step-rerank');
            if (step2 && step3 && !msg.classList.contains('done-generating')) {
                step2.classList.remove('active');
                step2.classList.add('complete');
                step3.classList.add('active');
            }
        }, 1100);

        return msg;
    };

    const updateStreamingBotMessage = (msg, text) => {
        const raw = parseActionExecutionBlocks(text || '').cleaned || '';
        // If a \`\`\`json block has opened but not yet closed, the JSON is incomplete.
        // Rendering partial JSON always fails and shows raw text — show a placeholder instead.
        const jsonOpenIdx = raw.lastIndexOf('\`\`\`json');
        const jsonCloseIdx = raw.lastIndexOf('\`\`\`', jsonOpenIdx + 6);
        const jsonIsPartial = jsonOpenIdx !== -1 && (jsonCloseIdx <= jsonOpenIdx);
        
        const isDeepSearch = msg.classList.contains('message-deep-search');
        let contentHtml = '';
        if (jsonIsPartial) {
            contentHtml = '<span class="flow-diagram-generating">&#9881; Generating diagram…</span>';
        } else {
            contentHtml = formatBotMessage(raw, { isDeepSearch });
        }
        
        let bodyEl = msg.querySelector('.message-body');
        if (!bodyEl && !isDeepSearch) {
            msg.innerHTML = `<div class="message-body"></div>`;
            bodyEl = msg.querySelector('.message-body');
        } else if (!bodyEl) {
            bodyEl = msg;
        }
        bodyEl.innerHTML = contentHtml;
        scrollMessagesToBottom();
    };

    const finalizeStreamingBotMessage = (msg, text, sources = [], usedExternalSearch = false, details = {}) => {
        msg.classList.remove('streaming', 'typing');
        const shouldShowLinks = userAskedForLinks(details.question || '');
        const actionBlocks = parseActionExecutionBlocks(text);
        const displayText = actionBlocks.cleaned || 'Review the autofill plan below.';
        const isDeepSearch = msg.classList.contains('message-deep-search');
        
        const contentHtml = formatBotMessage(displayText, { linkify: shouldShowLinks, isDeepSearch });
        
        if (isDeepSearch) {
            let headerHtml = `
                <div class="deep-search-header">
                    <span class="icon">🧠</span>
                    <span class="title">Aletheia Research Report</span>
                </div>
            `;
            
            if (details.deepSearchSummary) {
                const sum = details.deepSearchSummary;
                let covHtml = '';
                if (sum.coverage) {
                    covHtml = `
                        <div class="deep-search-coverage">
                            <h4>Research Coverage</h4>
                            <div class="coverage-grid">
                                ${Object.entries(sum.coverage).map(([k, v]) => `<div class="coverage-item ${v ? 'found' : 'missing'}"><span class="icon">${v ? '✓' : '✗'}</span> <span class="label">${k.charAt(0).toUpperCase() + k.slice(1)}</span></div>`).join('')}
                            </div>
                        </div>
                    `;
                }
                let missHtml = '';
                if (sum.missing_information && sum.missing_information.length > 0) {
                    missHtml = `
                        <div class="deep-search-missing-info">
                            <h4>Information Not Found</h4>
                            <ul>
                                ${sum.missing_information.map(info => `<li>${info}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                headerHtml += `
                    <div class="deep-search-summary">
                        <div class="stat"><span>Pages Crawled:</span> <strong>${sum.pages_crawled || 0}</strong></div>
                        <div class="stat"><span>Sources Used:</span> <strong>${sum.sources_used || 0}</strong></div>
                        <div class="stat"><span>Confidence:</span> <strong>${sum.confidence || 'N/A'}</strong></div>
                    </div>
                    ${covHtml}
                    ${missHtml}
                `;
            }
            msg.innerHTML = headerHtml + `<div class="message-body">${contentHtml}</div>`;
        } else {
            msg.innerHTML = `<div class="message-body">${contentHtml}</div>`;
        }
        
        appendActionConsentCard(msg, actionBlocks.actions);
        attachFlowDiagramQuestions(msg, details.question || '');
        appendModelBadge(msg, details);

        if (usedExternalSearch) {
            const badge = document.createElement('div');
            badge.className = 'external-search-indicator';
            badge.textContent = 'External Search Used';
            msg.prepend(badge);
        }

        if (shouldShowLinks) {
            appendOpenLinkButtons(msg, text);
        }
        if (shouldShowLinks) {
            appendSourceCards(msg, sources);
        }
        appendCopyButton(msg, text);
        appendFunctionalFeedback(msg, {
            url: activeScopeUrl,
            question: details.question || '',
            answer: text,
            provider: details.provider || '',
            model: details.model || '',
            sources,
            contentHash: details.contentHash || ''
        });
        appendFollowUpButtons(msg, details.followUps || []);
        const deliveredAt = Date.now();
        appendMessageTimestamp(msg, deliveredAt);
        scrollMessagesToBottom();
        saveChatMessage(text, 'bot', deliveredAt);
        rememberAssistantAnswer(details.memoryTurn, text, details, sources);
        window.setTimeout(() => autoHighlightAnswerMatch(details.question || '', text), 120);
    };

    const restoreStreamState = (state) => {
        let typing = messagesContainer.querySelector('.message.bot.typing');
        if (!typing) {
            typing = addMessage('', 'bot');
            typing.classList.add('typing');
        }
        typing.classList.remove('status-msg');
        
        activeResponseMessage = typing;
        activeBackendRequestId = state.requestId;
        const currentRequest = ++requestSerial;
        const restoredRequest = currentRequest;
        
        if (state.partialContent) {
            updateStreamingBotMessage(typing, state.partialContent);
        }
        
        if (state.status === 'completed' || state.status === 'error') {
            finalizeStreamingBotMessage(typing, state.partialContent || (state.status === 'error' ? 'Stream failed or was interrupted.' : ''), state.sources || [], false, {
                question: '', 
                provider: '',
                model: '',
                contentHash: ''
            });
            setSendButtonBusy(false);
            activeBackendRequestId = '';
        } else if (state.status === 'aborted') {
            typing.classList.remove('streaming', 'typing');
            typing.innerHTML = formatBotMessage(state.partialContent) + '<br><br><em>[Stream aborted]</em>';
            setSendButtonBusy(false);
            activeBackendRequestId = '';
        } else {
            // Stream is still active — wire up a live listener so incoming chunks continue to render.
            setSendButtonBusy(true);
            typing.classList.add('streaming');
            let liveAnswer = state.partialContent || '';
            const requestId = state.requestId;

            const liveListener = (message) => {
                if (!message || message.action !== 'chatStreamEvent' || message.requestId !== requestId) return;
                if (stoppedSerial === restoredRequest) {
                    chrome.runtime.onMessage.removeListener(liveListener);
                    return;
                }
                const event = message.event || {};
                if (event.type === 'delta') {
                    liveAnswer += event.text || '';
                    updateStreamingBotMessage(typing, liveAnswer);
                } else if (event.type === 'done' || event.type === 'error') {
                    chrome.runtime.onMessage.removeListener(liveListener);
                    finalizeStreamingBotMessage(typing, liveAnswer || (event.type === 'error' ? 'Stream interrupted.' : ''), event.sources || state.sources || [], false, {
                        provider: event.provider || '',
                        model: event.model || '',
                        question: '',
                        contentHash: ''
                    });
                    setSendButtonBusy(false);
                    activeBackendRequestId = '';
                    activeResponseMessage = null;
                }
            };
            chrome.runtime.onMessage.addListener(liveListener);
        }
    };

    const updateStatusMessage = (messageEl, text) => {
        if (!messageEl) return;
        const detailEl = messageEl.querySelector?.('.tool-status-detail');
        if (detailEl) {
            detailEl.textContent = text;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            return;
        }
        messageEl.innerText = text;
        appendMessageTimestamp(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    const addToolStatusMessage = (toolName, detail = 'Working...') => {
        const msg = addMessage('', 'bot', { persist: false });
        msg.classList.add('tool-status-message', 'typing');
        const isAssistant = String(toolName || '').toLowerCase() === 'assistant';
        const title = isAssistant ? 'Processing Request' : `Using ${toolName}`;

        if (isAssistant) {
            msg.innerHTML = `
                <div class="processing-status-widget" role="status" aria-live="polite">
                    <div class="psw-header">
                        <span class="psw-title">${escapeHtml(title)}</span>
                        <span class="psw-loader"></span>
                    </div>
                    <div class="psw-steps">
                        <div class="psw-step step-retrieval active">
                            <span class="psw-step-bullet"></span>
                            <span class="psw-step-text">Searching database and local page cache...</span>
                        </div>
                        <div class="psw-step step-web">
                            <span class="psw-step-bullet"></span>
                            <span class="psw-step-text">Fetching external web results if needed...</span>
                        </div>
                        <div class="psw-step step-rerank">
                            <span class="psw-step-bullet"></span>
                            <span class="psw-step-text">Ranking matching sections and validation...</span>
                        </div>
                        <div class="psw-step step-generation">
                            <span class="psw-step-bullet"></span>
                            <span class="psw-step-text">Drafting final answer using LLM...</span>
                        </div>
                    </div>
                </div>
            `;
            setTimeout(() => {
                const step1 = msg.querySelector('.step-retrieval');
                const step2 = msg.querySelector('.step-web');
                if (step1 && step2) {
                    step1.classList.remove('active');
                    step1.classList.add('complete');
                    step2.classList.add('active');
                }
            }, 550);
            setTimeout(() => {
                const step2 = msg.querySelector('.step-web');
                const step3 = msg.querySelector('.step-rerank');
                if (step2 && step3) {
                    step2.classList.remove('active');
                    step2.classList.add('complete');
                    step3.classList.add('active');
                }
            }, 1100);
        } else {
            msg.innerHTML = `
                <div class="tool-status-card" role="status" aria-live="polite">
                    <span class="tool-status-spinner" aria-hidden="true"></span>
                    <span class="tool-status-copy">
                        <span class="tool-status-title">${escapeHtml(title)}</span>
                        <span class="tool-status-detail">${escapeHtml(detail)}</span>
                    </span>
                </div>
            `;
        }
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return msg;
    };

    const addAnswerStatusMessage = (documentMode, detail = '') => {
        const initialDetail = detail || (
            documentMode === 'compare'
                ? 'Checking both sources for the answer...'
                : documentMode === 'document'
                ? 'Looking through the uploaded document...'
                : 'Reading the current page...'
        );
        return addToolStatusMessage('Assistant', initialDetail);
    };

    const answerGenerationStatus = (documentMode, allowExternalSearch = false) => {
        if (documentMode === 'compare') return 'Comparing the relevant document and page details...';
        if (documentMode === 'document') return 'Preparing an answer from the document...';
        if (allowExternalSearch) return 'Checking the page first, then approved web results if needed...';
        return 'Looking for the answer in the page context...';
    };

    const updateIndexProgress = (messageEl, text) => {
        setIndexStatus(text);
        if (messageEl) updateStatusMessage(messageEl, text);
    };

    const normalizeText = (text) => text.replace(/\s+/g, ' ').trim();

    const normalizeContentText = (text) => String(text || '')
        .split(/\n+/)
        .map((line) => normalizeText(line))
        .filter(Boolean)
        .join('\n');

    const uniqueLines = (items) => {
        const seen = new Set();
        const lines = [];

        items.join('\n').split('\n').forEach((line) => {
            const cleaned = normalizeText(line);
            if (!cleaned || cleaned.length < 2) return;

            const key = cleaned.toLowerCase();
            if (seen.has(key)) return;

            seen.add(key);
            lines.push(cleaned);
        });

        return lines.join('\n');
    };

    const isVisibleElement = (element) => {
        const style = window.getComputedStyle(element);
        return style.display !== 'none' &&
            style.visibility !== 'hidden' &&
            style.opacity !== '0' &&
            element.getClientRects().length > 0;
    };

    const isEnabledFormElement = (element) => {
        if (!element || element.disabled || element.readOnly) return false;
        if (element.closest('fieldset[disabled]')) return false;
        return isVisibleElement(element);
    };

    const labelForFormElement = (element) => {
        const id = element.id ? CSS.escape(element.id) : '';
        const labels = [];
        if (id) {
            document.querySelectorAll(`label[for="${id}"]`).forEach((label) => {
                labels.push(normalizeText(label.innerText || label.textContent || ''));
            });
        }
        if (element.closest('label')) {
            labels.push(normalizeText(element.closest('label').innerText || element.closest('label').textContent || ''));
        }
        const ariaLabelledBy = (element.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
        ariaLabelledBy.forEach((labelId) => {
            const labelEl = document.getElementById(labelId);
            if (labelEl) labels.push(normalizeText(labelEl.innerText || labelEl.textContent || ''));
        });
        labels.push(
            element.getAttribute('aria-label') || '',
            element.getAttribute('title') || '',
            element.getAttribute('name') || '',
            element.getAttribute('id') || ''
        );
        return labels.map(normalizeText).find(Boolean) || '';
    };

    let autofillElementRegistry = new Map();

    const registerAutofillField = (metadata, elements) => {
        const key = `field-${autofillElementRegistry.size + 1}`;
        autofillElementRegistry.set(key, { metadata, elements: Array.isArray(elements) ? elements : [elements] });
        return key;
    };

    const scrapePageInputs = () => {
        autofillElementRegistry = new Map();
        const inputs = [];
        const radioGroups = new Map();

        const addField = (element, typeOverride = '') => {
            if (!isEnabledFormElement(element)) return;
            const tag = element.tagName.toLowerCase();
            const type = (typeOverride || element.getAttribute('type') || tag).toLowerCase();
            if (['hidden', 'submit', 'button', 'reset', 'image', 'file', 'password'].includes(type)) return;
            const options = tag === 'select'
                ? Array.from(element.options || []).map((option) => normalizeText(option.textContent || option.value)).filter(Boolean)
                : [];
            const label = labelForFormElement(element);
            const metadata = {
                label,
                placeholder: element.getAttribute('placeholder') || '',
                type,
                required: Boolean(element.required || element.getAttribute('aria-required') === 'true'),
                options,
                selector_metadata: {
                    name: element.getAttribute('name') || '',
                    id: element.id || '',
                    autocomplete: element.getAttribute('autocomplete') || ''
                }
            };
            metadata.field_id = registerAutofillField(metadata, element);
            inputs.push(metadata);
        };

        document.querySelectorAll('input, textarea, select').forEach((element) => {
            if (container.contains(element)) return;
            const type = (element.getAttribute('type') || element.tagName).toLowerCase();
            if (type === 'radio') {
                if (!isEnabledFormElement(element)) return;
                const groupName = element.name || element.getAttribute('aria-label') || labelForFormElement(element) || `radio-${radioGroups.size + 1}`;
                if (!radioGroups.has(groupName)) radioGroups.set(groupName, []);
                radioGroups.get(groupName).push(element);
                return;
            }
            addField(element);
        });

        radioGroups.forEach((elements, groupName) => {
            const visibleElements = elements.filter(isEnabledFormElement);
            if (!visibleElements.length) return;
            const first = visibleElements[0];
            const metadata = {
                label: labelForFormElement(first) || groupName,
                placeholder: '',
                type: 'radio',
                required: visibleElements.some((element) => element.required || element.getAttribute('aria-required') === 'true'),
                options: visibleElements.map((element) => labelForFormElement(element) || element.value).filter(Boolean),
                selector_metadata: {
                    name: groupName,
                    id: first.id || '',
                    autocomplete: ''
                }
            };
            metadata.field_id = registerAutofillField(metadata, visibleElements);
            inputs.push(metadata);
        });

        return inputs.slice(0, 80);
    };

    const resolveNavigableUrl = (value) => {
        const trimmedValue = (value || '').trim();
        if (!trimmedValue || trimmedValue === '#' || trimmedValue.toLowerCase().startsWith('javascript:')) {
            return null;
        }

        try {
            const url = new URL(trimmedValue, window.location.href);
            return ['http:', 'https:', 'mailto:', 'tel:'].includes(url.protocol) ? url.href : null;
        } catch (error) {
            return null;
        }
    };

    const extractUrlFromOnclick = (onclickValue) => {
        const onclick = onclickValue || '';
        const patterns = [
            /(?:window\.)?location(?:\.href|\.assign|\.replace)?\s*(?:=|\()\s*['"]([^'"]+)['"]/i,
            /window\.open\(\s*['"]([^'"]+)['"]/i,
            /open\(\s*['"]([^'"]+)['"]/i
        ];

        for (const pattern of patterns) {
            const match = onclick.match(pattern);
            if (match && match[1]) {
                const resolvedUrl = resolveNavigableUrl(match[1]);
                if (resolvedUrl) return resolvedUrl;
            }
        }

        return null;
    };

    const getClickableDestination = (element) => {
        const directAttributes = [
            'href',
            'to',
            'routerlink',
            'data-href',
            'data-url',
            'data-link',
            'data-route',
            'data-path',
            'data-target-url',
            'data-redirect',
            'data-destination',
            'data-permalink',
            'formaction'
        ];

        for (const attribute of directAttributes) {
            const resolvedUrl = resolveNavigableUrl(element.getAttribute(attribute));
            if (resolvedUrl) return resolvedUrl;
        }

        const onclickUrl = extractUrlFromOnclick(element.getAttribute('onclick'));
        if (onclickUrl) return onclickUrl;

        const closestAnchor = element.closest('a[href], area[href]');
        if (closestAnchor) {
            return resolveNavigableUrl(closestAnchor.getAttribute('href'));
        }

        return null;
    };

    const getClickableLabel = (element, url) => {
        const text = normalizeText(
            element.innerText ||
            element.getAttribute('aria-label') ||
            element.getAttribute('title') ||
            element.getAttribute('alt') ||
            element.textContent ||
            ''
        );

        return text || url;
    };

    const addDiscoveredLink = (links, seen, element, type) => {
        if (!isVisibleElement(element)) return;

        const url = getClickableDestination(element);
        if (!url) return;

        const label = getClickableLabel(element, url);
        const key = `${label}|${url}`;
        if (seen.has(key)) return;

        seen.add(key);
        links.push({ label, url, type, element });
    };

    const extractPageLinks = () => {
        const links = [];
        const seen = new Set();

        document.querySelectorAll([
            'a[href]',
            'area[href]',
            '[role="link"]',
            '[to]',
            '[routerlink]',
            '[onclick]',
            '[data-href]',
            '[data-url]',
            '[data-link]',
            '[data-route]',
            '[data-path]',
            '[data-target-url]',
            '[data-redirect]',
            '[data-destination]',
            '[data-permalink]',
            'button[formaction]',
            'input[formaction]'
        ].join(',')).forEach((element) => {
            const type = element.matches('a[href], area[href]')
                ? 'anchor'
                : 'clickable redirect';
            addDiscoveredLink(links, seen, element, type);
        });

        return links.slice(0, MAX_INDEXED_LINKS);
    };

    const extractPageMetadata = () => {
        const parts = [];
        const addMeta = (label, selector, attribute = 'content') => {
            const value = document.querySelector(selector)?.getAttribute(attribute);
            if (value) parts.push(`${label}: ${value}`);
        };

        if (document.title) parts.push(`Title: ${document.title}`);
        addMeta('Description', 'meta[name="description"]');
        addMeta('Keywords', 'meta[name="keywords"]');
        addMeta('Open graph title', 'meta[property="og:title"]');
        addMeta('Open graph description', 'meta[property="og:description"]');
        addMeta('Canonical URL', 'link[rel="canonical"]', 'href');

        return uniqueLines(parts);
    };

    const extractMediaText = () => {
        const parts = [];

        document.querySelectorAll('img, picture, video, audio, iframe').forEach((element) => {
            if (shouldSkipContentElement(element) && element.tagName.toLowerCase() !== 'iframe') return;

            const label = [
                element.getAttribute('alt'),
                element.getAttribute('aria-label'),
                element.getAttribute('title'),
                element.getAttribute('name')
            ].filter(Boolean).join(' - ');
            const src = element.currentSrc || element.src || element.getAttribute('src') || '';
            if (label) parts.push(`Media: ${label}${src ? ` (${shortDisplayUrl(src, 70)})` : ''}`);
        });

        return uniqueLines(parts.slice(0, 120));
    };

    const extractTableText = () => {
        const tables = [];

        document.querySelectorAll('table, [role="table"], [role="grid"]').forEach((table, tableIndex) => {
            if (shouldSkipContentElement(table)) return;

            const rows = Array.from(table.querySelectorAll('tr, [role="row"]')).slice(0, 80);
            const rowText = rows.map((row) => {
                const cells = Array.from(row.querySelectorAll('th, td, [role="columnheader"], [role="rowheader"], [role="cell"], [role="gridcell"]'))
                    .map((cell) => normalizeText(cell.innerText || cell.textContent || ''))
                    .filter(Boolean);
                return cells.join(' | ');
            }).filter(Boolean);

            if (rowText.length) {
                tables.push(`Table ${tableIndex + 1}:\n${rowText.join('\n')}`);
            }
        });

        return uniqueLines(tables);
    };

    const extractSameOriginIframeText = () => {
        const parts = [];

        document.querySelectorAll('iframe').forEach((frame, index) => {
            if (!isVisibleElement(frame)) return;

            try {
                const frameDocument = frame.contentDocument;
                if (!frameDocument?.body) return;

                const frameText = normalizeContentText(frameDocument.body.innerText || frameDocument.body.textContent || '');
                if (frameText) {
                    parts.push(`Embedded frame ${index + 1}:\n${frameText}`);
                }
            } catch (error) {
                const label = frame.getAttribute('title') || frame.getAttribute('aria-label') || frame.getAttribute('name');
                const src = frame.getAttribute('src');
                if (label || src) {
                    parts.push(`Embedded frame ${index + 1}: ${[label, src && shortDisplayUrl(src, 70)].filter(Boolean).join(' - ')}`);
                }
            }
        });

        return uniqueLines(parts);
    };

    const extractPageControls = () => {
        const controls = [];
        const seen = new Set();

        document.querySelectorAll([
            'button',
            '[role="button"]',
            'input[type="button"]',
            'input[type="submit"]',
            '[aria-label]',
            '[title]'
        ].join(',')).forEach((element) => {
            if (!isVisibleElement(element)) return;

            const label = getClickableLabel(element, '');
            if (!label || label.length < 2) return;

            const url = getClickableDestination(element);
            const key = `${label}|${url || element.tagName}`;
            if (seen.has(key)) return;

            seen.add(key);
            controls.push({
                label,
                url,
                type: url ? 'clickable redirect' : 'component',
                element
            });
        });

        return controls.slice(0, MAX_INDEXED_LINKS);
    };

    const normalizeForAction = (text) => normalizeText(text)
        .toLowerCase()
        .replace(/[^a-z0-9\s/-]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

    const detectPageActionIntent = (question) => {
        const normalized = normalizeForAction(question);
        const navigationMatch = normalized.match(/\b(open|go to|navigate to|visit|show me|take me to)\b\s+(?:the\s+)?(.+)/);
        const siteSearchMatch = normalized.match(/\b(search|search for|look up)\b\s+(?:for\s+)?(.+)/);
        const searchMatch = normalized.match(/\b(find|look for|where is|where are|show|highlight|point to|locate)\b\s+(?:the\s+)?(.+)/);
        const explicitSiteSearch = /\b(on|in|within)\s+(this|the|current)\s+(website|site|page)\b|\b(search bar|site search|website search|current website|this website|this site|this page)\b/.test(normalized);
        const directFindTargets = [
            ['login', /\b(log in|login|sign in|signin)\b/],
            ['registration', /\b(register|registration|sign up|signup|create account|join now)\b/],
            ['apply', /\b(apply|apply now|application|submit application)\b/],
            ['enroll', /\b(enroll|enrol|admission|admissions)\b/],
            ['book', /\b(book|booking|reserve|reservation|schedule)\b/],
            ['download', /\b(download|get file|get pdf)\b/],
            ['buy', /\b(buy|purchase|order|checkout)\b/],
            ['donate', /\b(donate|donation|contribute)\b/],
            ['subscribe', /\b(subscribe|subscription|newsletter)\b/],
            ['links', /\b(links?|urls?|navigation)\b/],
            ['contact', /\b(contact|support|help)\b/],
            ['pricing', /\b(pricing|plans?|price)\b/]
        ];

        if (navigationMatch) {
            return { type: 'open', target: cleanupActionTarget(navigationMatch[2]) };
        }

        if (siteSearchMatch && explicitSiteSearch) {
            return { type: 'site-search', target: cleanupActionTarget(siteSearchMatch[2]) };
        }

        if (searchMatch) {
            return { type: 'find', target: cleanupActionTarget(searchMatch[2]) };
        }

        for (const [target, pattern] of directFindTargets) {
            const shortDirectAsk = pattern.test(normalized) && normalized.split(' ').length <= 3;
            if (pattern.test(normalized) && (normalized === target || shortDirectAsk || /\b(where|find|show|highlight|page|link|button)\b/.test(normalized))) {
                return { type: 'find', target };
            }
        }

        return null;
    };

    const cleanupActionTarget = (target) => normalizeForAction(target)
        .replace(/\b(on search bar|in search bar|on the search bar|in the search bar|search bar|page|links?|button|component|section|keyword|keywords|for this website|on this website|in this website|within this page|this website|website)\b/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

    const actionTokens = (text) => normalizeForAction(text)
        .split(' ')
        .filter((token) => token.length > 1 && !['the', 'this', 'that', 'page', 'link', 'links', 'button', 'component', 'keyword', 'keywords'].includes(token));

    const ACTION_ALIAS_GROUPS = {
        login: ['login', 'log in', 'signin', 'sign in', 'account'],
        registration: ['register', 'registration', 'signup', 'sign up', 'create account', 'join', 'join now'],
        apply: ['apply', 'apply now', 'application', 'submit application'],
        enroll: ['enroll', 'enrol', 'admission', 'admissions'],
        book: ['book', 'booking', 'reserve', 'reservation', 'schedule'],
        download: ['download', 'get file', 'get pdf'],
        buy: ['buy', 'purchase', 'order', 'checkout'],
        donate: ['donate', 'donation', 'contribute'],
        subscribe: ['subscribe', 'subscription', 'newsletter'],
        pricing: ['pricing', 'plans', 'price', 'cost'],
        contact: ['contact', 'support', 'help', 'email', 'phone'],
        dashboard: ['dashboard', 'portal', 'account']
    };

    const aliasGroupsForText = (text) => {
        const normalized = normalizeForAction(text);
        return Object.entries(ACTION_ALIAS_GROUPS)
            .filter(([, aliases]) => aliases.some((alias) => normalized.includes(alias)))
            .map(([group]) => group);
    };

    const containsAliasGroup = (text, group) => {
        const normalized = normalizeForAction(text);
        return (ACTION_ALIAS_GROUPS[group] || []).some((alias) => normalized.includes(alias));
    };

    const highlightTargetFromQuestion = (question, answer = '') => {
        const intent = detectPageActionIntent(question);
        if (intent?.target) return intent.target;

        const stopwords = new Set([
            'what', 'where', 'when', 'which', 'who', 'why', 'how',
            'is', 'are', 'was', 'were', 'do', 'does', 'did',
            'tell', 'show', 'find', 'explain', 'about', 'page',
            'website', 'site', 'current', 'this', 'that', 'there',
            'can', 'you', 'me', 'please', 'give', 'answer'
        ]);
        const questionTokens = normalizeForAction(question)
            .split(' ')
            .filter((token) => token.length > 2 && !stopwords.has(token));
        const answerTokens = normalizeForAction(answer)
            .split(' ')
            .filter((token) => token.length > 2 && !stopwords.has(token));
        const answerSet = new Set(answerTokens);
        const sharedTokens = questionTokens.filter((token) => answerSet.has(token));
        const tokens = sharedTokens.length ? sharedTokens : questionTokens;

        return tokens.slice(0, 5).join(' ');
    };

    const scoreActionCandidate = (candidate, target) => {
        const targetText = normalizeForAction(target);
        const label = normalizeForAction(candidate.label || '');
        const url = normalizeForAction(candidate.url || '');
        const haystack = `${label} ${url}`;
        const tokens = actionTokens(targetText);
        const requestedGroups = aliasGroupsForText(targetText);
        const candidateGroups = aliasGroupsForText(haystack);

        if (!tokens.length) return 0;
        let score = 0;
        if (label === targetText) score += 12;
        if (label.includes(targetText)) score += 8;
        if (url.includes(targetText.replace(/\s+/g, '-')) || url.includes(targetText.replace(/\s+/g, ''))) score += 6;

        tokens.forEach((token) => {
            if (label.split(' ').includes(token)) score += 4;
            else if (label.includes(token)) score += 2;
            if (url.includes(token)) score += 1;
        });

        requestedGroups.forEach((group) => {
            if (containsAliasGroup(haystack, group)) {
                score += 8;
            }
        });

        candidateGroups.forEach((group) => {
            if (requestedGroups.length && !requestedGroups.includes(group)) {
                score -= 4;
            }
        });

        if (requestedGroups.length && !requestedGroups.some((group) => containsAliasGroup(haystack, group))) {
            score -= 5;
        }

        const purposeTokens = tokens.filter((token) => !['now', 'here', 'start', 'continue'].includes(token));
        if (purposeTokens.length >= 2) {
            const matchedPurposeTokens = purposeTokens.filter((token) => haystack.includes(token)).length;
            if (matchedPurposeTokens === 0) {
                score -= 3;
            }
        }

        return score;
    };

    const findActionMatches = (target, includeControls = true) => {
        const candidates = [
            ...extractPageLinks(),
            ...(includeControls ? extractPageControls() : [])
        ];

        return candidates
            .map((candidate) => ({ ...candidate, score: scoreActionCandidate(candidate, target) }))
            .filter((candidate) => candidate.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 6);
    };

    const detectLinkFinderToolIntent = (question) => {
        const normalized = normalizeForAction(question);
        const explicitLinkAsk = /\b(link|links|url|urls|href|website link|page link|contact link|pricing link|login link|download link|important links|all links)\b/.test(normalized);
        if (!explicitLinkAsk) return null;

        const targetMatch = normalized.match(/\b(?:find|show|get|list|give|open|where is|where are)\b\s+(?:me\s+)?(?:the\s+)?(.+?)(?:\s+(?:link|links|url|urls))?$/);
        const target = cleanupActionTarget(targetMatch?.[1] || normalized)
            .replace(/\b(find|show|get|list|give|open|where is|where are|me|all|important|urls?|links?|href)\b/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

        return {
            type: 'link_finder',
            query: target || 'links'
        };
    };

    const classifyLinkMatch = (candidate) => {
        const haystack = normalizeForAction(`${candidate.label || ''} ${candidate.url || ''}`);
        if (/\b(contact|support|help|email|phone)\b/.test(haystack)) return 'contact';
        if (/\b(price|pricing|plans?|cost|billing)\b/.test(haystack)) return 'pricing';
        if (/\b(login|log in|signin|sign in|account|dashboard|portal)\b/.test(haystack)) return 'login';
        if (/\b(register|signup|sign up|apply|enroll|admission)\b/.test(haystack)) return 'action';
        if (/\b(download|pdf|file|brochure|report)\b/.test(haystack)) return 'download';
        if (/\b(doc|docs|documentation|guide|learn|resources?)\b/.test(haystack)) return 'resource';
        return candidate.type || 'link';
    };

    const runLinkFinderTool = (query) => {
        const target = normalizeForAction(query || 'links');
        const links = extractPageLinks();
        const controlsWithUrls = extractPageControls().filter((item) => item.url);
        const candidates = [...links, ...controlsWithUrls];
        const allMode = !target || target === 'links' || target === 'all' || target === 'important';

        const matches = candidates
            .map((candidate) => {
                const score = allMode
                    ? (candidate.type === 'anchor' ? 4 : 2)
                    : scoreActionCandidate(candidate, target);
                return {
                    ...candidate,
                    score,
                    category: classifyLinkMatch(candidate),
                    confidence: Math.max(0.1, Math.min(0.98, score / 16))
                };
            })
            .filter((candidate) => candidate.url && (allMode || candidate.score > 0))
            .sort((a, b) => b.score - a.score)
            .slice(0, allMode ? 10 : 6);

        return {
            tool: 'link_finder',
            query: query || 'links',
            total_links: links.length,
            matches
        };
    };

    const addLinkFinderToolCard = (result) => {
        const msg = document.createElement('div');
        msg.className = 'message bot link-finder-tool-card';
        const title = result.matches.length
            ? `Found ${result.matches.length} link${result.matches.length === 1 ? '' : 's'} for "${result.query}"`
            : `No matching links found for "${result.query}"`;

        msg.innerHTML = `
            <h4>Link Finder Tool</h4>
            <p>${escapeHtml(title)}${result.total_links ? ` from ${result.total_links} visible page links.` : '.'}</p>
        `;

        if (result.matches.length) {
            const actions = document.createElement('div');
            actions.className = 'message-link-actions';

            result.matches.forEach((match, index) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.title = match.url;
                button.innerHTML = `
                    <span class="link-label">${escapeHtml(match.label || `Link ${index + 1}`)}</span>
                    <span class="link-url">${escapeHtml(shortDisplayUrl(match.url))}</span>
                `;
                button.onclick = () => {
                    addHumanReviewCard({
                        intent: { type: 'open', target: match.label || match.url },
                        match,
                        onApprove: () => {
                            addMessage(`Opening ${shortDisplayUrl(match.url)}...`, 'bot', { persist: false });
                            window.open(match.url, '_blank', 'noopener,noreferrer');
                        }
                    });
                };
                actions.appendChild(button);
            });

            msg.appendChild(actions);
        }

        appendCopyButton(
            msg,
            result.matches.map((match) => `${match.label || 'Link'}: ${match.url}`).join('\n') || title
        );
        messagesContainer.appendChild(msg);
        scrollMessagesToBottom();
        return msg;
    };

    const handleLinkFinderTool = (question) => {
        const intent = detectLinkFinderToolIntent(question);
        if (!intent) return false;

        const status = addToolStatusMessage('Link Finder Tool', 'Scanning visible links...');
        const result = runLinkFinderTool(intent.query);
        status.remove();
        addLinkFinderToolCard(result);
        return true;
    };

    const detectPageSummarizerToolIntent = (question) => {
        const normalized = normalizeForAction(question);
        if (!/\b(summarize|summary|tldr|tl dr|key takeaways|takeaways|main points|quick overview|page overview)\b/.test(normalized)) {
            return null;
        }
        if (/\b(document|resume|pdf|uploaded|compare)\b/.test(normalized) && activeDocumentMode !== 'website') {
            return null;
        }
        let summaryType = 'quick';
        if (/\b(key takeaways|takeaways|main points)\b/.test(normalized)) summaryType = 'takeaways';
        else if (/\b(detailed|full|complete|section wise|section-wise)\b/.test(normalized)) summaryType = 'detailed';
        else if (/\b(tldr|tl dr|brief|short)\b/.test(normalized)) summaryType = 'tldr';
        return { type: 'page_summarizer', summaryType };
    };

    const runPageSummarizerTool = async (question, options = {}) => {
        const intent = detectPageSummarizerToolIntent(question);
        if (!intent) return false;

        const status = addToolStatusMessage('Page Summarizer Tool', 'Reading page content...');
        try {
            await prepareLivePageContent(status);
            const modelRequest = selectedModelRequest();
            const result = await sendBackendMessage('fetchPageSummary', {
                url: activeScopeUrl,
                title: document.title || pageTopic(),
                content: latestContent,
                summary_type: intent.summaryType,
                ollama_model: modelRequest.ollama_model,
                openrouter_model: modelRequest.openrouter_model,
                force_provider: options.forceProvider || modelRequest.force_provider
            });
            status.remove();
            await addBotMessageAnimated(
                result.answer || 'I could not summarize this page.',
                [],
                false,
                {
                    provider: result.provider || 'Summarizer',
                    model: result.model || '',
                    confidence: 'high',
                    question,
                    contentHash: latestContentHash,
                    followUps: pageSpecificSuggestions(result.suggestions, 3)
                }
            );
            return true;
        } catch (error) {
            status.remove();
            console.warn('Page summarizer tool failed; falling back to normal chat.', error);
            return false;
        }
    };

    const findVisibleTextMatches = (target) => {
        const selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'li', 'dt', 'dd',
            'label', 'legend',
            'summary',
            'td', 'th',
            '[role="heading"]',
            '[aria-label]',
            '[title]'
        ].join(',');
        const seen = new Set();

        return Array.from(document.querySelectorAll(selectors))
            .filter((element) => !container.contains(element) && isVisibleElement(element))
            .map((element) => {
                const label = normalizeText(
                    element.innerText ||
                    element.getAttribute('aria-label') ||
                    element.getAttribute('title') ||
                    element.textContent ||
                    ''
                );
                if (!label || label.length < 2) return null;

                const key = `${label}|${element.tagName}`;
                if (seen.has(key)) return null;
                seen.add(key);

                return {
                    label: label.length > 120 ? `${label.slice(0, 117)}...` : label,
                    snippet: label.length > 260 ? `${label.slice(0, 257)}...` : label,
                    type: 'page text',
                    element,
                    score: scoreActionCandidate({ label, url: '' }, target)
                };
            })
            .filter((candidate) => candidate && candidate.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 6);
    };

    const isConfidentMatch = (best, second) => {
        if (!best) return false;
        return best.score >= 8 && (!second || best.score >= second.score + 3);
    };

    const findTextSnippets = (target) => {
        const visibleMatches = findVisibleTextMatches(target);
        if (visibleMatches.length) {
            return visibleMatches.map((match) => match.snippet).slice(0, 3);
        }

        const text = getCachedPageContent();
        const normalizedText = normalizeForAction(text);
        const normalizedTarget = normalizeForAction(target);
        const tokens = actionTokens(normalizedTarget);
        const snippets = [];
        const seen = new Set();

        if (!tokens.length) return snippets;

        const searchTerms = [normalizedTarget, ...tokens].filter((term) => term.length > 2);
        searchTerms.forEach((term) => {
            const index = normalizedText.indexOf(term);
            if (index < 0) return;

            const start = Math.max(0, index - 120);
            const end = Math.min(text.length, index + term.length + 180);
            const snippet = normalizeText(text.slice(start, end));
            if (!snippet || seen.has(snippet)) return;

            seen.add(snippet);
            snippets.push(snippet);
        });

        return snippets.slice(0, 3);
    };

    const isElementActuallySearchInput = (element) => {
        if (!element || !isVisibleElement(element)) return false;
        if (container.contains(element)) return false;

        const tag = element.tagName.toLowerCase();
        const type = (element.getAttribute('type') || '').toLowerCase();
        const role = (element.getAttribute('role') || '').toLowerCase();
        const combined = normalizeForAction([
            element.getAttribute('name'),
            element.getAttribute('id'),
            element.getAttribute('aria-label'),
            element.getAttribute('placeholder'),
            element.getAttribute('title'),
            element.className,
            role,
            type
        ].join(' '));

        if (tag === 'input' && ['search', 'text', ''].includes(type) && /\b(search|query|q|keyword|find)\b/.test(combined)) {
            return true;
        }

        if (tag === 'textarea' && /\b(search|query|keyword|find)\b/.test(combined)) {
            return true;
        }

        if (element.isContentEditable && (role === 'searchbox' || /\b(search|query)\b/.test(combined))) {
            return true;
        }

        return role === 'searchbox';
    };

    const findSiteSearchInput = () => {
        const selectors = [
            'input[type="search"]',
            'input[name="q"]',
            'input[name="search"]',
            'input[aria-label*="search" i]',
            'input[placeholder*="search" i]',
            'textarea[aria-label*="search" i]',
            '[role="searchbox"]',
            'form[role="search"] input',
            'form[action*="search" i] input',
            'form[action*="results" i] input',
            'form[action*="results" i] textarea'
        ];

        for (const selector of selectors) {
            const inputEl = Array.from(document.querySelectorAll(selector)).find(isElementActuallySearchInput);
            if (inputEl) return inputEl;
        }

        return Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"]')).find(isElementActuallySearchInput) || null;
    };

    const setNativeInputValue = (element, value) => {
        if (element.isContentEditable) {
            element.focus();
            element.textContent = value;
            element.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
            return;
        }

        const prototype = element.tagName === 'TEXTAREA'
            ? window.HTMLTextAreaElement.prototype
            : window.HTMLInputElement.prototype;
        const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');

        element.focus();
        if (descriptor?.set) {
            descriptor.set.call(element, value);
        } else {
            element.value = value;
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
    };

    const submitSiteSearch = (searchInput) => {
        const form = searchInput.closest('form');
        if (form) {
            if (typeof form.requestSubmit === 'function') {
                form.requestSubmit();
            } else {
                form.submit();
            }
            return;
        }

        searchInput.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
        }));
    };

    const highlightActionElement = (element) => {
        element.classList.add('web-chatbot-action-highlight', 'autofill-highlight');
        element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        window.setTimeout(() => {
            element.classList.remove('web-chatbot-action-highlight', 'autofill-highlight');
        }, 2200);
    };

    const normalizeFieldText = (value = '') => String(value || '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ' ')
        .trim();

    const scoreAutofillField = (metadata = {}, target = '') => {
        const targetText = normalizeFieldText(target);
        if (!targetText) return 0;
        const haystack = normalizeFieldText([
            metadata.label,
            metadata.placeholder,
            metadata.selector_metadata?.name,
            metadata.selector_metadata?.id,
            metadata.selector_metadata?.autocomplete
        ].join(' '));
        if (!haystack) return 0;
        if (haystack === targetText) return 100;
        if (haystack.includes(targetText) || targetText.includes(haystack)) return 70;
        const targetTokens = new Set(targetText.split(/\s+/).filter((token) => token.length > 1));
        const fieldTokens = new Set(haystack.split(/\s+/).filter((token) => token.length > 1));
        let score = 0;
        targetTokens.forEach((token) => {
            if (fieldTokens.has(token)) score += 12;
        });
        return score;
    };

    const resolveAutofillField = (action = {}) => {
        const fieldName = action.field || action.label || action.placeholder || '';
        const entries = Array.from(autofillElementRegistry.values());
        return entries
            .map((entry) => ({ ...entry, score: scoreAutofillField(entry.metadata, fieldName) }))
            .sort((a, b) => b.score - a.score)[0] || null;
    };

    const validateElement = (element) => Boolean(element && isEnabledFormElement(element));

    const setSelectValue = (element, value) => {
        const wanted = normalizeFieldText(value);
        const option = Array.from(element.options || []).find((item) =>
            normalizeFieldText(item.value) === wanted || normalizeFieldText(item.textContent) === wanted
        ) || Array.from(element.options || []).find((item) =>
            normalizeFieldText(item.value).includes(wanted) || normalizeFieldText(item.textContent).includes(wanted)
        );
        if (!option) return false;
        element.focus();
        element.value = option.value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    };

    const valueForUndo = (element) => {
        if (!element) return '';
        if (element.type === 'checkbox' || element.type === 'radio') return Boolean(element.checked);
        if (element.isContentEditable) return element.textContent || '';
        return element.value || '';
    };

    const restoreAutofillValue = (element, value) => {
        if (!element) return;
        if (element.type === 'checkbox' || element.type === 'radio') {
            element.checked = Boolean(value);
            element.dispatchEvent(new Event('change', { bubbles: true }));
            return;
        }
        setNativeInputValue(element, value);
    };

    const applyAutofillAction = async (action, statusEl, undoStack) => {
        const actionRisk = analyzeAutofillActionRisk(action);
        if (actionRisk.blocked) {
            if (statusEl) statusEl.textContent = `${action.field || 'Sensitive field'} blocked`;
            return false;
        }

        const resolved = resolveAutofillField(action);
        if (!resolved || resolved.score < 8) {
            if (statusEl) statusEl.textContent = `${action.field || 'Field'} not found`;
            return false;
        }
        if (isSensitiveAutofillTarget([
            resolved.metadata?.label,
            resolved.metadata?.placeholder,
            resolved.metadata?.type,
            resolved.metadata?.selector_metadata?.name,
            resolved.metadata?.selector_metadata?.id,
            resolved.metadata?.selector_metadata?.autocomplete
        ].join(' '))) {
            if (statusEl) statusEl.textContent = `${action.field || resolved.metadata?.label || 'Sensitive field'} blocked`;
            return false;
        }

        const elements = resolved.elements.filter(validateElement);
        if (!elements.length) {
            if (statusEl) statusEl.textContent = `${action.field || resolved.metadata.label || 'Field'} not found`;
            return false;
        }

        const type = String(action.type || 'fill').toLowerCase();
        const value = String(action.value ?? '');
        if (statusEl) statusEl.textContent = `Filling ${action.field || resolved.metadata.label || 'field'}`;

        let changed = false;
        if (resolved.metadata.type === 'radio') {
            const selected = elements.find((element) => scoreAutofillField({ label: labelForFormElement(element), placeholder: element.value }, value) > 0);
            if (selected) {
                undoStack.push({ element: selected, oldValue: valueForUndo(selected) });
                highlightActionElement(selected);
                selected.checked = true;
                selected.dispatchEvent(new Event('change', { bubbles: true }));
                changed = true;
            }
        } else {
            const element = elements[0];
            undoStack.push({ element, oldValue: valueForUndo(element) });
            highlightActionElement(element);
            if (element.tagName === 'SELECT' || type === 'select') {
                changed = setSelectValue(element, value);
            } else if (type === 'check' || type === 'uncheck' || element.type === 'checkbox') {
                element.checked = type === 'uncheck' ? false : !/^(false|no|off|0)$/i.test(value);
                element.dispatchEvent(new Event('change', { bubbles: true }));
                changed = true;
            } else {
                setNativeInputValue(element, value);
                changed = true;
            }
        }

        await new Promise((resolve) => window.setTimeout(resolve, 180));
        return changed;
    };

    const actionsFromConsentCard = (card) => {
        let originalActions = [];
        try {
            originalActions = JSON.parse(card.dataset.originalActions || '[]');
        } catch (error) {
            originalActions = [];
        }

        return Array.from(card.querySelectorAll('.action-row'))
            .map((row) => {
                const index = Number(row.dataset.actionIndex || 0);
                const original = originalActions[index] || {};
                const include = row.querySelector('.action-include-input');
                if (!include || !include.checked || include.disabled) return null;
                const field = row.querySelector('.action-field-input')?.value?.trim() || original.field || '';
                const value = row.querySelector('.action-value-input')?.value ?? original.value ?? '';
                const edited = field !== (original.field || '') || String(value) !== String(original.value ?? '');
                const action = {
                    ...original,
                    field,
                    value,
                    confidence: edited ? Math.max(Number(original.confidence || 0), AUTOFILL_LOW_CONFIDENCE_THRESHOLD) : original.confidence
                };
                return analyzeAutofillActionRisk(action).blocked ? null : action;
            })
            .filter(Boolean);
    };

    const previewAutofillPlan = (card) => {
        const actions = actionsFromConsentCard(card);
        const statusEl = card.querySelector('.action-status');
        if (!actions.length) {
            if (statusEl) statusEl.textContent = 'No enabled mappings to preview.';
            return;
        }

        let matched = 0;
        actions.forEach((action) => {
            const resolved = resolveAutofillField(action);
            if (resolved && isSensitiveAutofillTarget([
                resolved.metadata?.label,
                resolved.metadata?.placeholder,
                resolved.metadata?.type,
                resolved.metadata?.selector_metadata?.name,
                resolved.metadata?.selector_metadata?.id,
                resolved.metadata?.selector_metadata?.autocomplete
            ].join(' '))) return;
            const element = resolved?.elements?.find(validateElement);
            if (!element || resolved.score < 8) return;
            matched += 1;
            highlightActionElement(element);
        });
        if (statusEl) statusEl.textContent = `Preview matched ${matched}/${actions.length} enabled fields.`;
        saveAutofillSession(actions, 'preview');
    };

    const formCompletionReport = () => {
        const required = Array.from(document.querySelectorAll('input, textarea, select'))
            .filter((element) => !container.contains(element))
            .filter((element) => (element.required || element.getAttribute('aria-required') === 'true') && isEnabledFormElement(element));

        const emptyRequired = required.filter((element) => {
            const type = (element.getAttribute('type') || '').toLowerCase();
            if (type === 'checkbox' || type === 'radio') {
                const name = element.name;
                if (name) {
                    return !Array.from(document.querySelectorAll(`input[name="${CSS.escape(name)}"]`)).some((candidate) => candidate.checked);
                }
                return !element.checked;
            }
            return !String(element.value || '').trim();
        });

        return {
            required: required.length,
            remaining: emptyRequired.length,
            complete: emptyRequired.length === 0,
            labels: emptyRequired.map(labelForFormElement).filter(Boolean).slice(0, 5)
        };
    };

    const detectNextStepControls = () => Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], a[role="button"]'))
        .filter((element) => !container.contains(element) && isVisibleElement(element))
        .filter((element) => /\b(next|continue|save and continue|review|proceed)\b/i.test(element.innerText || element.value || element.getAttribute('aria-label') || ''))
        .slice(0, 3);

    const showAutofillUndoBanner = (undoStack = []) => {
        if (!undoStack.length) return;
        const banner = document.createElement('div');
        banner.className = 'undo-banner';
        banner.innerHTML = '<span>Autofill complete</span><button type="button">Undo Autofill</button>';
        banner.querySelector('button').onclick = () => {
            undoStack.slice().reverse().forEach(({ element, oldValue }) => restoreAutofillValue(element, oldValue));
            banner.remove();
            addMessage('Autofill undone.', 'bot', { persist: false });
        };
        messagesContainer.appendChild(banner);
        scrollMessagesToBottom(true);
        window.setTimeout(() => banner.remove(), 30000);
    };

    const executeAutofillPlan = async (card) => {
        const actions = actionsFromConsentCard(card);
        const approveButton = card.querySelector('.action-approve');
        const previewButton = card.querySelector('.action-preview');
        const cancelButton = card.querySelector('.action-cancel');
        const statusEl = card.querySelector('.action-status');
        if (!actions.length) {
            if (statusEl) statusEl.textContent = 'No enabled mappings to fill. Review low-confidence rows first.';
            return;
        }
        approveButton.disabled = true;
        if (previewButton) previewButton.disabled = true;
        if (cancelButton) cancelButton.disabled = true;
        const undoStack = [];
        let completed = 0;
        for (let index = 0; index < actions.length; index += 1) {
            const action = actions[index];
            if (statusEl) statusEl.textContent = `Step ${index + 1}/${actions.length}`;
            const ok = await applyAutofillAction(action, statusEl, undoStack);
            if (ok) completed += 1;
        }
        const report = formCompletionReport();
        if (statusEl) {
            statusEl.textContent = report.complete
                ? `Filled ${completed}/${actions.length} fields. Required fields look complete.`
                : `Filled ${completed}/${actions.length} fields. ${report.remaining} required field${report.remaining === 1 ? '' : 's'} still need review.`;
        }
        const nextControls = detectNextStepControls();
        if (nextControls.length && !card.querySelector('.action-session-note')) {
            const note = document.createElement('div');
            note.className = 'action-session-note';
            note.textContent = 'Multi-step session active. Review this page, then continue to the next step manually and ask Aletheia to autofill again.';
            card.appendChild(note);
        }
        card.classList.add('executed');
        saveAutofillSession(actions, 'filled');
        showAutofillUndoBanner(undoStack);
    };

    const performSiteSearch = (query) => {
        const searchInput = findSiteSearchInput();
        if (!searchInput) return false;

        highlightActionElement(searchInput);
        setNativeInputValue(searchInput, query);
        addMessage(`Searching for "${query}"...`, 'bot', { persist: false });
        window.setTimeout(() => submitSiteSearch(searchInput), 700);
        return true;
    };

    const actionDescription = (intent, match = null) => {
        if (intent?.type === 'site-search') {
            return `search this website for "${intent.target}"`;
        }

        const label = match?.label || intent?.target || 'this item';
        if (match?.url) {
            return `open "${label}"`;
        }
        if (match?.element) {
            return `open or highlight "${label}"`;
        }
        return `continue with "${label}"`;
    };

    const performMatchedPageAction = (intent, match) => {
        if (!match) return;

        if (match.url) {
            addMessage(`Opening ${match.label || match.url}...`, 'bot', { persist: false });
            window.setTimeout(() => {
                window.location.href = match.url;
            }, 500);
            return;
        }

        if (match.element) {
            addMessage(`Opening ${match.label || intent.target}...`, 'bot', { persist: false });
            highlightActionElement(match.element);
            window.setTimeout(() => {
                match.element.click();
            }, 700);
        }
    };

    const addActionMatchesMessage = (intro, matches, intent) => {
        const msg = addMessage(intro, 'bot', { persist: false });
        const actions = document.createElement('div');
        actions.className = 'message-link-actions';

        matches.forEach((match, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = match.label || (match.url ? `Link ${index + 1}` : `Component ${index + 1}`);
            button.onclick = () => {
                if (intent.type === 'find' && match.element && !match.url) {
                    highlightActionElement(match.element);
                    addMessage(`Highlighted "${match.label || intent.target}" on this page.`, 'bot', { persist: false });
                    return;
                }

                addHumanReviewCard({
                    intent,
                    match,
                    onApprove: () => performMatchedPageAction(intent, match)
                });
            };
            actions.appendChild(button);
        });

        msg.appendChild(actions);
        scrollMessagesToBottom();
    };

    const addHumanReviewCard = ({ intent, match, onApprove }) => {
        const card = document.createElement('div');
        card.className = 'human-review-card';

        const title = document.createElement('h4');
        title.textContent = 'Confirm action';

        const details = document.createElement('p');
        details.textContent = `Please check this first. I will ${actionDescription(intent, match)} only after you approve.`;

        const actions = document.createElement('div');
        actions.className = 'human-review-actions';

        const approve = document.createElement('button');
        approve.className = 'btn-approve-action';
        approve.type = 'button';
        approve.textContent = 'Approve';

        const cancel = document.createElement('button');
        cancel.className = 'btn-cancel-action';
        cancel.type = 'button';
        cancel.textContent = 'Cancel';

        approve.onclick = () => {
            card.remove();
            onApprove();
        };

        cancel.onclick = () => {
            card.remove();
            addMessage('Action cancelled.', 'bot', { persist: false });
        };

        actions.appendChild(approve);
        actions.appendChild(cancel);
        card.appendChild(title);
        card.appendChild(details);
        card.appendChild(actions);
        messagesContainer.appendChild(card);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    // Cache search provider config — loaded once on init
    let _searchConfig = { tavily_available: false, primary_provider: 'none' };
    const loadSearchConfig = async () => {
        try {
            const cfg = await sendBackendMessage('fetchSearchConfig', {});
            if (cfg && !cfg.error) _searchConfig = cfg;
        } catch (_) {}
    };
    loadSearchConfig();

    const addExternalSearchReviewCard = ({ question, onApprove }) => {
        const isTavily = _searchConfig.tavily_available;
        const providerName = isTavily ? 'Tavily' : 'Web Search';
        const providerDesc = isTavily
            ? 'AI-powered search — fast, accurate, real-time'
            : 'External web search';
        const fallbackNote = '';

        const card = document.createElement('div');
        card.className = 'external-search-permission-card';
        card.innerHTML = `
            <div class="esp-header">
                <span class="esp-title">Not enough info on this page</span>
            </div>
            <p class="esp-desc">I couldn't find enough information on this page to answer <strong>&ldquo;${escapeHtml(question)}&rdquo;</strong> well.</p>
            <div class="esp-provider-box">
                <span class="esp-provider-name">${escapeHtml(providerName)}</span>
                <span class="esp-provider-desc">${escapeHtml(providerDesc)}</span>
                ${fallbackNote ? `<span class="esp-provider-fallback">${escapeHtml(fallbackNote)}</span>` : ''}
            </div>
            <p class="esp-ask">May I search the web to find a better answer?</p>
            <div class="esp-actions">
                <button class="esp-btn-approve" type="button">Search with ${escapeHtml(providerName)}</button>
                <button class="esp-btn-cancel" type="button">Stay on page</button>
            </div>
        `;
        card.querySelector('.esp-btn-approve').onclick = () => { card.remove(); onApprove(); };
        card.querySelector('.esp-btn-cancel').onclick = () => {
            card.remove();
            addMessage('Okay, I will only use content from this page.', 'bot', { persist: false });
        };
        messagesContainer.appendChild(card);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    const handleLocalPageAction = (question) => {
        const intent = detectPageActionIntent(question);
        if (!intent || !intent.target) return false;

        if (intent.type === 'site-search' && findSiteSearchInput()) {
            addHumanReviewCard({
                intent,
                match: { label: `Search: ${intent.target}` },
                onApprove: () => performSiteSearch(intent.target)
            });
            return true;
        }

        const actionMatches = findActionMatches(intent.target, intent.type !== 'open');
        const textMatches = intent.type === 'find' ? findVisibleTextMatches(intent.target) : [];
        const matches = [...actionMatches, ...textMatches]
            .sort((a, b) => b.score - a.score)
            .slice(0, 6);

        if (!matches.length) {
            const snippets = ['find', 'site-search'].includes(intent.type) ? findTextSnippets(intent.target) : [];
            if (snippets.length) {
                addMessage(`I found this page content matching "${intent.target}":\n\n- ${snippets.join('\n\n- ')}`, 'bot', { persist: false });
                return true;
            }

            addMessage(`I couldn't find a visible link, component, or text matching "${intent.target}" on this page.`, 'bot', { persist: false });
            return true;
        }

        if (intent.type === 'open') {
            const navigable = matches.filter((match) => match.url);
            const best = navigable[0] || matches[0];
            const second = navigable[1] || matches[1];
            const confident = isConfidentMatch(best, second);

            if (confident && (best.url || best.element)) {
                addHumanReviewCard({
                    intent,
                    match: best,
                    onApprove: () => performMatchedPageAction(intent, best)
                });
                return true;
            }

            addActionMatchesMessage(`I found a few possible matches for "${intent.target}". Choose one to review:`, navigable.length ? navigable : matches, intent);
            return true;
        }

        const best = matches[0];
        if (intent.type === 'find' && best?.element) {
            highlightActionElement(best.element);
            addMessage(`I found and highlighted the best match for "${intent.target}": **${best.label || best.snippet || intent.target}**`, 'bot', { persist: false });
            return true;
        }

        addActionMatchesMessage(`I found these matches for "${intent.target}". Choose one to review:`, matches, intent);
        return true;
    };

    const autoHighlightAnswerMatch = (question, answer = '') => {
        if (activeDocumentMode !== 'website' || activeScope !== 'page') return false;

        const target = highlightTargetFromQuestion(question, answer);
        if (!target || target.length < 2) return false;

        const matches = [
            ...findVisibleTextMatches(target),
            ...findActionMatches(target, true)
        ].sort((a, b) => b.score - a.score);
        const best = matches[0];
        const second = matches[1];

        if (!best?.element || best.score < 4) return false;

        highlightActionElement(best.element);
        return true;
    };

    const findDocumentTextMatches = (target) => {
        const text = uploadedDocument?.extracted_text || '';
        const tokens = actionTokens(target);
        if (!text || !tokens.length) return [];

        const lines = text
            .split(/\n+/)
            .map((line) => normalizeText(line))
            .filter((line) => line.length >= 2);
        const seen = new Set();

        return lines
            .map((line, index) => {
                const normalizedLine = normalizeForAction(line);
                let score = 0;
                const targetText = normalizeForAction(target);
                if (normalizedLine === targetText) score += 12;
                if (normalizedLine.includes(targetText)) score += 8;
                tokens.forEach((token) => {
                    if (normalizedLine.split(' ').includes(token)) score += 4;
                    else if (normalizedLine.includes(token)) score += 2;
                });
                return { line, line_number: index + 1, score };
            })
            .filter((match) => match.score > 0 && !seen.has(match.line.toLowerCase()) && seen.add(match.line.toLowerCase()))
            .sort((a, b) => b.score - a.score)
            .slice(0, 5);
    };

    const handleLocalDocumentFind = (question) => {
        const intent = detectPageActionIntent(question);
        if (!intent || !intent.target || intent.type === 'open' || intent.type === 'site-search') return false;
        if (!uploadedDocument?.extracted_text) return false;

        const matches = findDocumentTextMatches(intent.target);
        if (!matches.length) {
            addMessage(`I couldn't find an exact text match for "${intent.target}" in **${uploadedDocument.filename || 'the uploaded document'}**.`, 'bot', { persist: false });
            return true;
        }

        const lines = matches.map((match) => `- ${match.line}`).join('\n');
        addMessage(`I found exact document matches for "${intent.target}" in **${uploadedDocument.filename || 'the uploaded document'}**:\n\n${lines}`, 'bot', { persist: false });
        return true;
    };

    const buildIndexedContent = (forceRefresh = false) => {
        const pageText = getCachedPageContent(forceRefresh);
        const links = extractPageLinks();

        const header = `Indexed URL: ${window.location.href}\nPage title: ${document.title || window.location.href}\nExtractor version: ${INDEX_SCHEMA_VERSION}\n\n`;

        if (!links.length) {
            return `${header}${pageText}`;
        }

        const linkText = links
            .map((link, index) => `Link ${index + 1}: ${link.label}\nType: ${link.type}\nURL: ${link.url}`)
            .join('\n\n');

        return `${header}${pageText}\n\nPage links:\n${linkText}`;
    };

    const warmLazyPageContent = async () => {
        const originalX = window.scrollX;
        const originalY = window.scrollY;
        const maxScroll = Math.max(
            document.documentElement.scrollHeight,
            document.body.scrollHeight,
            window.innerHeight
        ) - window.innerHeight;

        if (maxScroll <= window.innerHeight * 0.75) return;

        const steps = Math.min(6, Math.max(2, Math.ceil(maxScroll / Math.max(window.innerHeight, 1))));
        for (let index = 1; index <= steps; index += 1) {
            window.scrollTo(originalX, Math.round((maxScroll * index) / steps));
            await new Promise((resolve) => setTimeout(resolve, 120));
        }

        window.scrollTo(originalX, originalY);
        await new Promise((resolve) => setTimeout(resolve, 180));
    };

    const waitForPageToSettle = () => new Promise((resolve) => {
        let settledTimer = null;
        let finished = false;
        const observer = new MutationObserver(() => {
            if (settledTimer) clearTimeout(settledTimer);
            settledTimer = setTimeout(finish, 350);
        });

        const finish = () => {
            if (finished) return;
            finished = true;
            if (settledTimer) clearTimeout(settledTimer);
            observer.disconnect();
            resolve();
        };

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });

        settledTimer = setTimeout(finish, document.readyState === 'complete' ? 250 : 800);
        setTimeout(finish, 1800);
    });

    const getCachedPageContent = (forceRefresh = false) => {
        const now = Date.now();
        const cacheIsFresh = !forceRefresh &&
            pageContentCache.url === window.location.href &&
            pageContentCache.content &&
            now - Number(pageContentCache.cachedAt || 0) < 5000;

        if (cacheIsFresh) {
            latestContent = pageContentCache.content;
            latestContentUrl = window.location.href;
            return latestContent;
        }

        const content = extractPageContent();
        latestContent = content;
        latestContentUrl = window.location.href;
        latestContentHash = '';
        pageContentCache = {
            url: window.location.href,
            title: document.title || '',
            content,
            cachedAt: now,
            indexedContentHash: ''
        };
        try {
            sessionStorage.setItem(pageContentCacheKey, JSON.stringify(pageContentCache));
        } catch (error) {
            console.debug('Page content cache skipped:', error);
        }
        return content;
    };

    const shouldSkipContentElement = (element) => {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
        if (container.contains(element)) return true;
        if (element.matches('script, style, noscript, iframe, svg, canvas, template, [hidden], [aria-hidden="true"]')) {
            return true;
        }
        return !isVisibleElement(element);
    };

    const elementTextForContent = (element) => normalizeContentText([
        element.innerText,
        element.getAttribute('aria-label'),
        element.getAttribute('title'),
        element.getAttribute('alt'),
        element.getAttribute('placeholder'),
        element.value
    ].filter(Boolean).join('\n'));

    const textFromOpenShadowRoots = (root) => {
        const parts = [];
        root.querySelectorAll('*').forEach((element) => {
            if (!element.shadowRoot || shouldSkipContentElement(element)) return;
            const shadowText = extractVisibleContent(element.shadowRoot);
            if (shadowText) parts.push(shadowText);
        });
        return parts.join('\n');
    };

    const extractVisibleContent = (root) => {
        const parts = [];
        const seen = new Set();
        const selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'li', 'dt', 'dd', 'blockquote', 'figcaption',
            'summary', 'caption', 'th', 'td', 'pre', 'code',
            'div', 'span',
            'label', 'button', '[role="button"]', 'a[href]',
            'input', 'textarea', 'select', 'option', 'output',
            '[aria-label]', '[title]', '[placeholder]',
            'article', 'section', '[role="main"]', '[role="article"]',
            '[role="heading"]', '[role="region"]', '[role="tabpanel"]',
            '[role="listitem"]', '[role="cell"]', '[role="gridcell"]', '[role="row"]'
        ].join(',');

        root.querySelectorAll(selectors).forEach((element) => {
            if (shouldSkipContentElement(element)) return;
            if (element.closest('nav, header, footer, aside') && !element.matches('main *, article *, [role="main"] *')) {
                return;
            }

            const tag = element.tagName.toLowerCase();
            const role = element.getAttribute('role');
            const isContainer = ['article', 'section', 'div'].includes(tag) || ['main', 'article', 'listitem', 'row'].includes(role);
            const hasBlockChildren = Array.from(element.children || []).some((child) =>
                ['DIV', 'SECTION', 'ARTICLE', 'MAIN', 'P', 'UL', 'OL', 'TABLE'].includes(child.tagName)
            );
            const text = elementTextForContent(element);
            if (!text || text.length < 2) return;
            if (isContainer && text.length < 25) return;
            if (isContainer && hasBlockChildren && text.length > 1600) return;
            if (tag === 'span' && text.length > 500) return;

            const key = normalizeText(text).toLowerCase();
            if (seen.has(key)) return;
            seen.add(key);
            parts.push(text);
        });

        const shadowText = textFromOpenShadowRoots(root);
        if (shadowText) parts.push(shadowText);

        return parts.join('\n');
    };

    const extractPageContent = () => {
        const primaryRoot =
            document.querySelector('article') ||
            document.querySelector('main') ||
            document.querySelector('[role="main"]');

        const metadataText = extractPageMetadata();
        const primaryText = primaryRoot ? extractVisibleContent(primaryRoot) : '';
        const bodyText = extractVisibleContent(document.body);
        const fallbackText = normalizeContentText(document.body.innerText || document.body.textContent || '');
        const tableText = extractTableText();
        const mediaText = extractMediaText();
        const iframeText = extractSameOriginIframeText();
        const candidates = [metadataText, primaryText, bodyText, fallbackText, tableText, mediaText, iframeText].filter(Boolean);
        const merged = [];
        const seenLines = new Set();

        candidates.forEach((candidate) => {
            candidate.split('\n').forEach((line) => {
                const cleaned = normalizeContentText(line);
                if (!cleaned || cleaned.length < 2) return;

                const key = cleaned.toLowerCase();
                if (seenLines.has(key)) return;

                seenLines.add(key);
                merged.push(cleaned);
            });
        });

        const bestText = merged.length ? merged.join('\n') : (bodyText || primaryText || fallbackText);

        return bestText.slice(0, 180000);
    };

    const sha256 = async (text) => {
        const data = new TextEncoder().encode(normalizeText(text));
        const digest = await crypto.subtle.digest('SHA-256', data);
        return Array.from(new Uint8Array(digest))
            .map((byte) => byte.toString(16).padStart(2, '0'))
            .join('');
    };

    const sendBackendMessage = (action, payload) => new Promise((resolve, reject) => {
        const requestId = payload?.request_id || '';
        chrome.runtime.sendMessage({ action, payload, requestId }, (response) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message || 'Unknown extension messaging error.'));
                return;
            }

            if (response && response.error) {
                reject(new Error(response.error));
                return;
            }

            resolve(response || {});
        });
    });

    const streamBackendChat = (payload, onEvent) => new Promise((resolve, reject) => {
        const requestId = payload?.request_id || '';
        let settled = false;
        let sawDone = false;
        let idleTimer = null;

        const cleanup = () => {
            window.clearTimeout(idleTimer);
            chrome.runtime.onMessage.removeListener(listener);
        };

        const finish = (value) => {
            if (settled) return;
            settled = true;
            cleanup();
            resolve(value || {});
        };

        const fail = (error) => {
            if (settled) return;
            settled = true;
            cleanup();
            reject(error instanceof Error ? error : new Error(String(error || 'Streaming failed.')));
        };

        const refreshIdleTimer = () => {
            window.clearTimeout(idleTimer);
            idleTimer = window.setTimeout(() => {
                fail(new Error('Streaming response timed out before completion.'));
            }, 300000);
        };

        const listener = (message) => {
            if (!message || message.action !== 'chatStreamEvent' || message.requestId !== requestId) {
                return;
            }

            refreshIdleTimer();
            const event = message.event || {};
            onEvent(event);

            if (event.type === 'done') {
                sawDone = true;
                finish(event);
            } else if (event.type === 'error') {
                fail(new Error(event.message || 'Streaming failed.'));
            } else if (event.type === 'external_required') {
                finish({
                    requires_external_permission: true,
                    confidence: event.confidence,
                    sources: event.sources || [],
                    suggestions: event.suggestions || [],
                    metrics: event.metrics || {}
                });
            }
        };

        chrome.runtime.onMessage.addListener(listener);
        refreshIdleTimer();
        chrome.runtime.sendMessage({ action: 'fetchChatStream', payload, requestId }, (response) => {
            if (chrome.runtime.lastError) {
                fail(new Error(chrome.runtime.lastError.message || 'Unknown extension messaging error.'));
                return;
            }

            if (response && response.error && !sawDone) {
                fail(new Error(response.error));
            }
        });
    });

    const COMPARE_STREAM_TIMEOUT_MS = 900000;

    const streamBackendCompare = (payload, onEvent, requestId = '') => new Promise((resolve, reject) => {
        const streamRequestId = requestId || `compare-stream-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        let settled = false;
        let sawDone = false;
        let sawCompareResult = false;
        let idleTimer = null;

        const cleanup = () => {
            window.clearTimeout(idleTimer);
            chrome.runtime.onMessage.removeListener(listener);
        };

        const finish = (value) => {
            if (settled) return;
            settled = true;
            cleanup();
            resolve(value || {});
        };

        const fail = (error) => {
            if (settled) return;
            settled = true;
            cleanup();
            reject(error instanceof Error ? error : new Error(String(error || 'Compare streaming failed.')));
        };

        const partialFinish = (message) => {
            finish({
                type: 'compare_partial',
                message: message || 'The structured comparison is ready, but the final explanation timed out.'
            });
        };

        const refreshIdleTimer = () => {
            window.clearTimeout(idleTimer);
            idleTimer = window.setTimeout(() => {
                if (sawCompareResult) {
                    partialFinish('The structured comparison is ready, but the final explanation timed out. Local Ollama models can be slow on large sources.');
                } else {
                    fail(new Error('Compare is taking longer than expected. Local Ollama models can be slow on large sources. Try a smaller model or shorter sources.'));
                }
            }, COMPARE_STREAM_TIMEOUT_MS);
        };

        const listener = (message) => {
            if (!message || message.action !== 'compareStreamEvent' || message.requestId !== streamRequestId) {
                return;
            }

            refreshIdleTimer();
            const event = message.event || {};
            onEvent(event);

            if (event.type === 'compare_result') {
                sawCompareResult = true;
            } else if (event.type === 'compare_done') {
                sawDone = true;
                finish(event);
            } else if (event.type === 'error') {
                if (sawCompareResult) {
                    partialFinish(event.message || 'The structured comparison is ready, but the final explanation did not finish.');
                } else {
                    fail(new Error(event.message || 'Compare streaming failed.'));
                }
            }
        };

        chrome.runtime.onMessage.addListener(listener);
        refreshIdleTimer();
        chrome.runtime.sendMessage({ action: 'fetchCompareStream', payload, requestId: streamRequestId }, (response) => {
            if (chrome.runtime.lastError) {
                fail(new Error(chrome.runtime.lastError.message || 'Unknown extension messaging error.'));
                return;
            }

            if (response && response.error && !sawDone) {
                fail(new Error(response.error));
            }
        });
    });

    const setSendButtonBusy = (busy) => {
        sendBtn.classList.toggle('is-stopping', busy);
        sendBtn.disabled = false;
        sendBtn.title = busy ? 'Stop response' : 'Send';
        sendBtn.innerHTML = busy
            ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><rect x="7" y="7" width="10" height="10" rx="2"></rect></svg>'
            : '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
    };

    const abortCurrentRequest = () => {
        if (!activeBackendRequestId) return;
        const requestId = activeBackendRequestId;
        stoppedSerial = requestSerial;
        setIndexStatus('Stopping...');
        chrome.runtime.sendMessage({
            action: 'fetchCancel',
            payload: { request_id: requestId },
            requestId
        }, () => {
            chrome.runtime.sendMessage({ action: 'abortRequest', requestId });
        });
    };

    const ensureIndexed = async (force = false, statusMessage = null, requestId = '') => {
        if (!force && activeScopeUrl !== window.location.href && indexedContentHash) {
            setIndexStatus('Using site index');
            return indexedContentHash;
        }

        if (!force && indexingPromise) {
            setIndexStatus('Indexing already running');
            return indexingPromise;
        }

        updateIndexProgress(statusMessage, 'Reading page...');
        if (force) {
            pageContentCache = {};
            sessionStorage.removeItem(pageContentCacheKey);
        } else {
            await waitForPageToSettle();
        }
        await warmLazyPageContent();

        latestContent = buildIndexedContent(true);
        const currentHash = await sha256(latestContent);
        latestContentHash = currentHash;
        latestContentUrl = window.location.href;

        // After indexing, detect PDF/DOCX/TXT links and ask permission
        detectAndPromptPageDocuments();
        pageContentCache = {
            ...pageContentCache,
            url: window.location.href,
            title: document.title || '',
            cachedAt: Date.now(),
            indexedContentHash: currentHash
        };
        try {
            sessionStorage.setItem(pageContentCacheKey, JSON.stringify(pageContentCache));
        } catch (error) {
            console.debug('Page content cache skipped:', error);
        }

        if (!force && indexedContentHash === currentHash) {
            setIndexStatus('Using cached page index');
            return currentHash;
        }

        updateIndexProgress(statusMessage, 'Checking page index...');
        indexingPromise = sendBackendMessage('fetchCacheStatus', {
            request_id: requestId,
            url: window.location.href,
            content_hash: currentHash
        }).then((status) => {
            if (status.current) {
                updateIndexProgress(statusMessage, `Using cached page index (${status.chunks || 0} chunks)`);
                return { content_hash: currentHash };
            }

            updateIndexProgress(
                statusMessage,
                latestContent.length < 120 ? 'Page has very little readable text...' : 'Indexing page...'
            );
            return sendBackendMessage('fetchIndex', {
                request_id: requestId,
                url: activeScopeUrl,
                content: latestContent
            });
        }).then((result) => {
            indexedContentHash = result.content_hash || currentHash;
            if (activeScope === 'page') {
                pageContentHash = indexedContentHash;
            }
            setIndexStatus(result.indexed ? `Page indexed (${result.chunks || 0} chunks)` : 'Using cached page index');
            return indexedContentHash;
        }).finally(() => {
            indexingPromise = null;
        });

        return indexingPromise;
    };

    const startBackgroundPageIndexing = (delayMs = 1200) => {
        if (backgroundIndexStarted || !autoIndexInput.checked) return;
        backgroundIndexStarted = true;

        const run = () => {
            if (!autoIndexInput.checked || activeScope !== 'page') {
                backgroundIndexStarted = false;
                return;
            }

            ensureIndexed(false, null, `preindex-${Date.now()}`).catch((error) => {
                backgroundIndexStarted = false;
                console.debug('Background page indexing skipped:', error);
            });
        };

        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(() => window.setTimeout(run, delayMs), { timeout: 5000 });
        } else {
            window.setTimeout(run, delayMs);
        }
    };

    const prepareLivePageContent = async (statusMessage = null) => {
        if (latestContent && latestContentUrl === window.location.href && latestContentHash) {
            updateIndexProgress(statusMessage, 'Using prepared page content');
            return latestContentHash;
        }

        updateIndexProgress(statusMessage, 'Reading page...');
        await waitForPageToSettle();
        await warmLazyPageContent();

        latestContent = buildIndexedContent(true);
        const currentHash = await sha256(latestContent);
        latestContentHash = currentHash;
        latestContentUrl = window.location.href;
        pageContentCache = {
            ...pageContentCache,
            url: window.location.href,
            title: document.title || '',
            cachedAt: Date.now(),
            indexedContentHash: currentHash
        };
        try {
            sessionStorage.setItem(pageContentCacheKey, JSON.stringify(pageContentCache));
        } catch (error) {
            console.debug('Page content cache skipped:', error);
        }
        setIndexStatus('Using live page content');
        return currentHash;
    };

    const detectFlowchartToolIntent = (question) => {
        const text = ` ${String(question || '').toLowerCase()} `;
        return [
            'flowchart',
            'flow chart',
            'flow diagram',
            'roadmap',
            'road map',
            'mind map',
            'mindmap',
            'timeline',
            'user journey',
            'user flow',
            'sitemap',
            'org chart',
            'sequence diagram',
            'process map',
            'process flow',
            'process diagram',
            'decision tree',
            'concept map',
            'architecture flow',
            'system flow',
            'generate diagram',
            'create diagram',
            'make diagram',
            'draw diagram',
            'diagram for',
            'diagram of'
        ].some((term) => text.includes(term));
    };

    const detectChartToolIntent = (question) => {
        if (detectFlowchartToolIntent(question)) return false;
        const text = ` ${String(question || '').toLowerCase()} `;
        const graphOnly = /\bgraph\b/.test(text);
        const visualCue = /\b(show|make|create|generate|draw|visualize|visualise|plot|chart|comparison|score|breakdown|analytics|dashboard)\b/.test(text);
        return [
            'chart',
            'bar chart',
            'horizontal bar',
            'radar chart',
            'pie chart',
            'donut chart',
            'line chart',
            'plot',
            'visualize',
            'visualise',
            'score breakdown',
            'comparison graph',
            'comparison chart',
            'show graph',
            'show chart',
            'analytics dashboard'
        ].some((term) => text.includes(term)) || (graphOnly && visualCue);
    };

    const detectWorkflowDiscoveryIntent = (question) => {
        if (detectFlowchartToolIntent(question) || detectChartToolIntent(question)) return false;
        const text = ` ${String(question || '').toLowerCase()} `;
        return [
            // Original process terms
            'how do i apply',
            'how can i apply',
            'how to apply',
            'how do i register',
            'how to register',
            'how do i enroll',
            'how to enroll',
            'how do i submit',
            'what is the process',
            'what is the procedure',
            'application process',
            'admission process',
            'registration process',
            'enrollment process',
            'visa process',
            'tender process',
            'onboarding process',
            'step by step',
            'from start to finish',
            'complete workflow',
            'full workflow',
            'end to end process',
            // Login / sign-in explanations
            'how do i login',
            'how do i log in',
            'how do i sign in',
            'how to login',
            'how to log in',
            'how to sign in',
            'login process',
            'sign in process',
            'how do i register',
            'how to register',
            'how do i sign up',
            'how to sign up',
            'how to create an account',
            'how do i create an account',
            'account creation process',
            'registration steps',
            'signup process',
            // Concept / idea explanation requests
            'can you explain',
            'explain how',
            'explain the',
            'tell me how',
            'tell me about',
            'how does it work',
            'how does this work',
            'what is the concept',
            'what is the idea',
            'what is the purpose',
            'guide me through',
            'walk me through',
            'what are the steps',
            'steps to',
            'steps for',
            'what happens after',
            'what happens when',
            'what happens next',
            'breakdown of',
            'guide me on',
            'guide me about',
        ].some((term) => text.includes(term));
    };

    const runWorkflowDiscoveryTool = async (question, options = {}) => {
        if (!options.forceWorkflowDiscovery && !detectWorkflowDiscoveryIntent(question)) {
            return false;
        }

        const status = addToolStatusMessage('Workflow Discovery', 'Crawling related pages and documents...');
        setSendButtonBusy(true);

        try {
            const modelRequest = selectedModelRequest();
            const result = await sendBackendMessage('fetchWorkflowDiscovery', {
                request_id: `workflow-${Date.now()}-${++requestSerial}`,
                url: window.location.href,
                question,
                max_pages: Math.max(3, Math.min(Number(crawlLimitInput.value) || 18, 25)),
                max_documents: 8,
                ollama_model: modelRequest.ollama_model,
                openrouter_model: modelRequest.openrouter_model,
                force_provider: options.forceProvider || modelRequest.force_provider
            });

            status.remove();
            if (!result.ok) {
                addMessage(`Workflow Discovery could not reconstruct the process yet: ${result.error || 'No workflow was found.'}`, 'bot', { persist: false });
                return true;
            }

            if (result.site_url) {
                activeScopeUrl = result.site_url;
                siteContentHash = result.content_hash || siteContentHash;
                indexedContentHash = siteContentHash;
                setScope('site');
                setIndexStatus(`Workflow context indexed (${result.pages || 0} pages${result.documents ? `, ${result.documents} documents` : ''})`);
            }

            const crawlNote = `\n\n---\n**Workflow context:** indexed ${result.pages || 0} pages${result.documents ? ` and ${result.documents} linked documents` : ''}. Follow-up questions will use this crawled site context.`;
            await addBotMessageAnimated(
                `${result.answer || ''}${crawlNote}`,
                result.sources || [],
                false,
                {
                    provider: result.provider,
                    model: result.model,
                    confidence: 'workflow discovery',
                    question,
                    contentHash: result.content_hash || '',
                    followUps: pageSpecificSuggestions(result.suggestions || [], 3)
                }
            );
            return true;
        } catch (error) {
            status.remove();
            addMessage('Workflow Discovery failed: ' + error.message, 'bot', { persist: false });
            return true;
        } finally {
            setSendButtonBusy(false);
        }
    };

    const runChartTool = async (question, options = {}) => {
        if (!options.forceChart && !detectChartToolIntent(question)) {
            return false;
        }

        if (activeDocumentMode === 'document' && !uploadedDocument) {
            addMessage('Upload a document first, then I can build a chart from it.', 'bot', { persist: false });
            fileInput.click();
            return true;
        }

        const status = addToolStatusMessage('Chart Tool', 'Preparing chart context...');
        setSendButtonBusy(true);

        try {
            const needsWebsiteContext = activeDocumentMode !== 'document';
            const contentHash = needsWebsiteContext ? await prepareLivePageContent(status) : '';
            updateStatusMessage(status, 'Generating information chart...');
            const modelRequest = selectedModelRequest();
            const result = await sendBackendMessage('fetchChart', {
                url: activeScopeUrl,
                title: document.title || '',
                content: needsWebsiteContext && activeScope === 'page' ? latestContent : '',
                question,
                content_hash: contentHash,
                ollama_model: modelRequest.ollama_model,
                openrouter_model: modelRequest.openrouter_model,
                force_provider: options.forceProvider || modelRequest.force_provider,
                document_id: uploadedDocument?.document_id || '',
                document_mode: activeDocumentMode,
                fetched_webpage_text: fetchedWebpageText || '',
                fetched_webpage_url: fetchedWebpageUrl || '',
                conversation_memory: conversationMemorySnapshot(activeDocumentMode),
                history: modeScopedHistory(activeDocumentMode)
            });

            status.remove();
            if (!result.ok) {
                addMessage(`Chart Tool could not create a valid chart yet: ${result.error || result.warning || 'Generation was incomplete.'}`, 'bot', { persist: false });
                return true;
            }

            await addBotMessageAnimated(
                result.answer,
                result.sources || [],
                false,
                {
                    provider: result.provider,
                    model: result.model,
                    confidence: `${result.mode || activeDocumentMode} chart`.trim(),
                    question,
                    contentHash: latestContentHash,
                    followUps: pageSpecificSuggestions(['Show another chart', 'Explain this chart', 'Compare as table'], 3)
                }
            );
            return true;
        } catch (error) {
            status.remove();
            addMessage('Chart Tool could not create the chart: ' + error.message, 'bot', { persist: false });
            return true;
        } finally {
            setSendButtonBusy(false);
        }
    };



    const defaultChartPrompt = () => {
        if (activeDocumentMode === 'document') {
            return 'Create a chart that visualizes the most important information in this document.';
        }
        return 'Create a chart that visualizes the most important information on this page.';
    };

    // ── Search Mode Card (Quick vs Deep) ─────────────────────────────────

    // ── Search Mode Card (Quick vs Deep) ─────────────────────────────────

    const showSearchModeCard = (question, options = {}) => new Promise((resolve) => {
        const card = document.createElement('div');
        card.className = 'search-mode-card';
        card.innerHTML = `
            <div class="smc-header">
                <span class="smc-title">Search Options</span>
            </div>
            <p class="smc-question">&ldquo;${escapeHtml(question.length > 80 ? question.slice(0, 80) + '\u2026' : question)}&rdquo;</p>
            <div class="smc-options">
                <button class="smc-btn smc-btn-quick" type="button">
                    <span class="smc-btn-body">
                        <span class="smc-btn-title">Quick Search</span>
                        <span class="smc-btn-desc">Fast answers in seconds &bull; Top pages only</span>
                    </span>
                </button>
                <button class="smc-btn smc-btn-deep" type="button">
                    <span class="smc-btn-body">
                        <span class="smc-btn-title">Deep Search</span>
                        <span class="smc-btn-desc">Research-grade analysis &bull; Workflow discovery &bull; Entire website</span>
                    </span>
                    <span class="smc-badge">Premium</span>
                </button>
            </div>
        `;

        messagesContainer.appendChild(card);
        scrollMessagesToBottom();

        const cleanup = () => card.remove();

        card.querySelector('.smc-btn-quick').onclick = () => {
            cleanup();
            handleSend(question, { ...options, searchMode: 'quick', skipSearchChoice: true, skipUserEcho: true });
            resolve();
        };

        card.querySelector('.smc-btn-deep').onclick = () => {
            cleanup();
            showDeepSearchInitialization(question, options);
            resolve();
        };
    });

    const showDeepSearchInitialization = (question, options = {}) => {
        const card = document.createElement('div');
        card.className = 'search-mode-card';
        card.innerHTML = `
            <div class="smc-header">
                <span class="smc-title">Deep Search Scope</span>
            </div>
            <div style="margin: 10px 0; font-size: 12.5px; color: var(--cb-text-main); line-height: 1.55;">
                <strong>Estimated Scope:</strong>
                <ul style="margin: 8px 0; padding-left: 18px; list-style-type: disc;">
                    <li>Comprehensive multi-page website analysis</li>
                    <li>Workflow and requirement discovery enabled</li>
                    <li>Research-grade answer generation</li>
                </ul>
            </div>
            <button class="esp-btn-approve start-deep-btn" type="button" style="width: 100%; height: 36px; margin-top: 10px; cursor: pointer;">Start Deep Search</button>
        `;
        messagesContainer.appendChild(card);
        scrollMessagesToBottom();

        card.querySelector('.start-deep-btn').onclick = () => {
            card.remove();
            runDeepSearch(question, options);
        };
    };

    const runDeepSearch = async (question, options = {}) => {
        const progressEl = document.createElement('div');
        progressEl.className = 'deep-search-progress';
        progressEl.innerHTML = `
            <div class="dsp-header">
                <span class="dsp-header-title">Deep Search Progress</span>
            </div>
            <div class="dsp-steps">
                <div class="dsp-step phase-1 dsp-step-active">
                    <span class="dsp-step-icon">1</span>
                    <div class="dsp-step-details">
                        <span class="dsp-step-title">Crawling Website</span>
                        <span class="dsp-step-subtitle">Discovering pages and building sitemap</span>
                    </div>
                    <span class="dsp-counter crawl-counter">Pages Discovered: 1</span>
                </div>
                <div class="dsp-step phase-2">
                    <span class="dsp-step-icon">2</span>
                    <div class="dsp-step-details">
                        <span class="dsp-step-title">Indexing Content</span>
                        <span class="dsp-step-subtitle">Cleaning sections and building context</span>
                    </div>
                    <span class="dsp-counter index-counter">Sections: 0</span>
                </div>
                <div class="dsp-step phase-3">
                    <span class="dsp-step-icon">3</span>
                    <div class="dsp-step-details">
                        <span class="dsp-step-title">Extracting Entities</span>
                        <span class="dsp-step-subtitle">Finding requirements, documents, & deadlines</span>
                    </div>
                    <span class="dsp-counter entity-counter">Entities: 0</span>
                </div>
                <div class="dsp-step phase-4">
                    <span class="dsp-step-icon">4</span>
                    <div class="dsp-step-details">
                        <span class="dsp-step-title">Building Knowledge Graph</span>
                        <span class="dsp-step-subtitle">Connecting topics and dependencies</span>
                    </div>
                </div>
                <div class="dsp-step phase-5">
                    <span class="dsp-step-icon">5</span>
                    <div class="dsp-step-details">
                        <span class="dsp-step-title">Synthesizing Insights</span>
                        <span class="dsp-step-subtitle">Generating final structured answer</span>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(progressEl);
        scrollMessagesToBottom();

        // Phase 1: Crawl website
        const crawlInterval = setInterval(() => {
            const counter = progressEl.querySelector('.crawl-counter');
            if (counter) {
                const current = parseInt(counter.textContent.replace('Pages Discovered: ', '')) || 0;
                if (current < 18) {
                    counter.textContent = `Pages Discovered: ${current + 1}`;
                }
            }
        }, 400);

        try {
            const crawlResult = await sendBackendMessage('fetchCrawl', {
                url: activeScopeUrl,
                max_pages: 20,
            });
            clearInterval(crawlInterval);

            if (crawlResult.error) {
                progressEl.remove();
                addMessage(`Deep search failed: ${crawlResult.error}`, 'bot', { persist: false });
                return;
            }

            const totalPages = (crawlResult.pages || []).length || 15;
            progressEl.querySelector('.crawl-counter').textContent = `Pages Discovered: ${totalPages}`;
            const step1 = progressEl.querySelector('.phase-1');
            step1.classList.remove('dsp-step-active');
            step1.classList.add('dsp-step-complete');

            // Phase 2: Indexing
            const step2 = progressEl.querySelector('.phase-2');
            step2.classList.add('dsp-step-active');
            const totalSections = totalPages * 6;
            await new Promise(r => {
                let sections = 0;
                const indexInterval = setInterval(() => {
                    sections += Math.min(12, totalSections - sections);
                    progressEl.querySelector('.index-counter').textContent = `Sections Indexed: ${sections}`;
                    if (sections >= totalSections) {
                        clearInterval(indexInterval);
                        r();
                    }
                }, 100);
            });
            step2.classList.remove('dsp-step-active');
            step2.classList.add('dsp-step-complete');

            // Phase 3: Entity Extraction
            const step3 = progressEl.querySelector('.phase-3');
            step3.classList.add('dsp-step-active');
            const totalEntities = Math.round(18 + totalPages * 1.5);
            await new Promise(r => {
                let entities = 0;
                const entityInterval = setInterval(() => {
                    entities += Math.min(3, totalEntities - entities);
                    progressEl.querySelector('.entity-counter').textContent = `Entities Found: ${entities}`;
                    if (entities >= totalEntities) {
                        clearInterval(entityInterval);
                        r();
                    }
                }, 80);
            });
            step3.classList.remove('dsp-step-active');
            step3.classList.add('dsp-step-complete');

            // Phase 4: Knowledge Graph Construction
            const step4 = progressEl.querySelector('.phase-4');
            step4.classList.add('dsp-step-active');
            await new Promise(r => setTimeout(r, 1200));
            step4.classList.remove('dsp-step-active');
            step4.classList.add('dsp-step-complete');

            // Phase 5: Synthesis
            const step5 = progressEl.querySelector('.phase-5');
            step5.classList.add('dsp-step-active');
            await new Promise(r => setTimeout(r, 500));

            // Clean up stepper and send chat payload
            progressEl.remove();

            await handleSend(question, {
                ...options,
                searchMode: 'deep',
                skipSearchChoice: true,
                skipUserEcho: true,
                forceDeepContext: true,
            });
        } catch (err) {
            clearInterval(crawlInterval);
            progressEl.remove();
            addMessage(`Deep search failed: ${err.message}`, 'bot', { persist: false });
        }
    };

    // ── end Search Mode Card ─────────────────────────────────

    const runFlowchartTool = async (question, options = {}) => {
        if (!detectFlowchartToolIntent(question) && !options.regenerateDiagram) {
            return false;
        }

        const status = addToolStatusMessage('Flowchart Tool', 'Reading page content...');
        setSendButtonBusy(true);

        try {
            await prepareLivePageContent(status);
            updateStatusMessage(status, 'Generating adaptive flowchart...');
            const modelRequest = selectedModelRequest();
            const result = await sendBackendMessage('fetchFlowchart', {
                url: activeScopeUrl,
                title: document.title || '',
                content: latestContent,
                question,
                ollama_model: modelRequest.ollama_model,
                openrouter_model: modelRequest.openrouter_model,
                force_provider: options.forceProvider || modelRequest.force_provider,
                document_id: uploadedDocument?.document_id || '',
                document_mode: activeDocumentMode,
                fetched_webpage_text: fetchedWebpageText || '',
                fetched_webpage_url: fetchedWebpageUrl || '',
                conversation_memory: conversationMemorySnapshot(activeDocumentMode),
                history: modeScopedHistory(activeDocumentMode),
                variant: options.regenerateDiagram ? 'regenerate with a different valid structure' : ''
            });

            status.remove();
            if (!result.ok) {
                addMessage(`Flowchart Tool could not create a valid diagram yet: ${result.error || 'Generation was incomplete.'}`, 'bot', { persist: false });
                setFollowUps(pageSpecificSuggestions(result.suggestions, 3));
                return true;
            }

            await addBotMessageAnimated(
                result.answer,
                [],
                false,
                {
                    provider: result.provider,
                    model: result.model,
                    confidence: `${result.diagram_kind || 'flowchart'} ${result.complexity || ''}`.trim(),
                    question,
                    contentHash: latestContentHash,
                    followUps: pageSpecificSuggestions(result.suggestions, 3)
                }
            );
            return true;
        } catch (error) {
            status.remove();
            addMessage('Flowchart Tool could not create the diagram: ' + error.message, 'bot', { persist: false });
            return true;
        } finally {
            setSendButtonBusy(false);
        }
    };

    const pageTopic = () => {
        const title = normalizeText(document.title || '');
        if (title) return title.split('|')[0].split('-')[0].trim().slice(0, 80);

        const heading = document.querySelector('h1, h2');
        return normalizeText(heading?.innerText || heading?.textContent || 'this page').slice(0, 80);
    };

    const pageQuestionKeywords = () => {
        const values = [pageTopic()];
        document.querySelectorAll('h1, h2, h3').forEach((heading) => {
            if (container.contains(heading) || !isVisibleElement(heading)) return;
            const text = normalizeText(heading.innerText || heading.textContent || '');
            if (text && text.length <= 90) values.push(text);
        });
        return [...new Set(values.join(' ')
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, ' ')
            .split(/\s+/)
            .filter((word) => word.length > 3 && !['this', 'that', 'with', 'from', 'page', 'website', 'home'].includes(word)))]
            .slice(0, 18);
    };

    const topPageHeadings = () => Array.from(document.querySelectorAll('h1, h2, h3'))
        .filter((heading) => !container.contains(heading) && isVisibleElement(heading))
        .map((heading) => normalizeText(heading.innerText || heading.textContent || ''))
        .filter((text) => text && text.length <= 80)
        .slice(0, 3);

    const compactQuestionTopic = (value) => {
        const text = normalizeText(value || '').replace(/\s+[|-]\s+.*$/, '').trim();
        if (!text) return 'this page';
        return text.length > 44 ? `${text.slice(0, 41).trim()}...` : text;
    };

    const cleanSuggestionQuestion = (value) => {
        const text = normalizeText(String(value || ''))
            .replace(/^(please\s+)?(can you|could you)\s+/i, '')
            .replace(/[?.!]*$/, '');
        if (!text) return '';
        const question = text.endsWith('?') ? text : `${text}?`;
        return question.length > 76 ? `${question.slice(0, 73).trim()}...?` : question;
    };

    const isPageSpecificQuestion = (question) => {
        const value = normalizeText(question || '').toLowerCase();
        if (!value) return false;
        const keywords = pageQuestionKeywords();
        return keywords.some((word) => value.includes(word));
    };

    const pageSpecificSuggestions = (suggestions = [], limit = 3) => {
        const topic = compactQuestionTopic(pageTopic() || 'this page');
        const text = (latestContent || getCachedPageContent() || '').toLowerCase();
        const links = extractPageLinks();
        const headings = topPageHeadings().map(compactQuestionTopic);
        const fallback = [
            `Summarize ${topic}`,
            `Key points from ${topic}`
        ];

        headings.forEach((heading) => {
            if (fallback.length < 5 && !heading.toLowerCase().includes(topic.toLowerCase())) {
                fallback.push(`Explain "${heading}"`);
            }
        });

        if (links.some((link) => /contact|support|email|phone/i.test(link.label))) {
            fallback.push(`Contact options on ${topic}`);
        }
        if (links.some((link) => /pricing|plans|cost/i.test(link.label)) || /\b(pricing|plans|cost)\b/.test(text)) {
            fallback.push(`Pricing details from ${topic}`);
        }
        if (links.some((link) => /login|sign in|signup|register|apply/i.test(link.label))) {
            fallback.push(`How to get started on ${topic}`);
        }
        if (/\b(feature|features|service|services|product|products)\b/.test(text)) {
            fallback.push(`Main features on ${topic}`);
        }

        const cleanedSuggestions = (Array.isArray(suggestions) ? suggestions : [])
            .map(cleanSuggestionQuestion)
            .filter((item) => item && isPageSpecificQuestion(item));

        return [...new Set([...cleanedSuggestions, ...fallback])]
            .map(cleanSuggestionQuestion)
            .filter(Boolean)
            .slice(0, limit);
    };

    const proactiveQuestions = () => {
        return pageSpecificSuggestions([], 3);
    };

    const showProactiveIntro = (contentHash = '') => {
        const marker = contentHash || `${window.location.href}:${document.title}`;
        if (proactiveShownForHash === marker) return;
        if (conversationHistory.some((entry) => entry.sender === 'user')) return;

        proactiveShownForHash = marker;
        sessionStorage.setItem(`web-chatbot-proactive:${window.location.href}`, marker);

        const topic = pageTopic();
        const questions = proactiveQuestions();
        const messageForQuestions = (items) =>
            `I scanned **${topic || 'this page'}** and found page-specific things you can ask about.\n\nTry asking:\n- ${items.join('\n- ')}`;
        const introMessage = addMessage(messageForQuestions(questions), 'bot', { persist: false });
        setFollowUps(questions);
        sendBackendMessage('fetchStarterQuestions', {
            url: activeScopeUrl,
            content_hash: contentHash,
            title: document.title || topic
        }).then((result) => {
            if (Array.isArray(result.suggestions) && result.suggestions.length) {
                const websiteQuestions = pageSpecificSuggestions(result.suggestions, 3);
                introMessage.innerHTML = formatBotMessage(messageForQuestions(websiteQuestions));
                setFollowUps(websiteQuestions);
            }
        }).catch((error) => {
            console.debug('Starter question generation skipped:', error);
        });
    };

    const setScope = (scope) => {
        activeScope = scope;
        scopeSelect.value = scope;

        if (scope === 'page') {
            activeScopeUrl = window.location.href;
            indexedContentHash = pageContentHash;
            setFollowUps(pageSpecificSuggestions([], 3));
        } else {
            activeScopeUrl = window.location.origin;
            indexedContentHash = siteContentHash;
            setFollowUps(pageSpecificSuggestions([], 3));
        }
    };

    const crawlWebsite = async (statusMessage = null, requestId = '') => {
        const maxPages = Math.max(1, Math.min(Number(crawlLimitInput.value) || 10, 25));
        updateStatusMessage(statusMessage, `Crawling website...`);
        setIndexStatus('Crawling website...');
        const result = await sendBackendMessage('fetchCrawl', {
            request_id: requestId,
            url: window.location.href,
            max_pages: maxPages
        });

        if (!result.content_hash) {
            throw new Error('No crawlable pages were indexed.');
        }

        activeScopeUrl = result.site_url || window.location.origin;
        siteContentHash = result.content_hash;
        indexedContentHash = siteContentHash;
        setScope('site');
        updateStatusMessage(statusMessage, `Indexed ${result.pages || 0} pages. Preparing...`);
        setIndexStatus(`Site indexed (${result.pages || 0} pages)`);
        return indexedContentHash;
    };

    const comparePreviewText = (label, text) => {
        const cleaned = normalizeText(text || '');
        if (!cleaned) return `${label}\nNo readable text selected yet.`;
        return `${label}\n${cleaned.slice(0, 180)}${cleaned.length > 180 ? '...' : ''}`;
    };

    const compareShortLabel = (label) => String(label || '')
        .replace(/^Uploaded document:\s*/i, '')
        .replace(/^Fetched webpage:\s*/i, '')
        .replace(/^Current page:\s*/i, '')
        .slice(0, 34) || 'not selected';

    const updateCompareToolPanel = () => {
        if (!compareToolPanel) return;
        compareAdvancedPanel?.classList.toggle('hidden', !compareAdvancedOpen);
        webpagePanel?.classList.toggle('hidden', activeDocumentMode !== 'compare' || !compareAdvancedOpen);
        if (compareToggleBtn) compareToggleBtn.textContent = compareAdvancedOpen ? 'Hide sources' : 'Change sources';

        const currentPageText = latestContent || getCachedPageContent() || '';
        const sourceALabel = compareSourceA === 'current'
            ? `Current page: ${pageTopic()}`
            : uploadedDocument?.filename
            ? `Uploaded document: ${uploadedDocument.filename}`
            : 'Uploaded document';
        const sourceAText = compareSourceA === 'current' ? currentPageText : uploadedDocument?.extracted_text || '';

        let sourceBLabel = 'Fetched webpage';
        let sourceBText = fetchedWebpageText || '';
        if (compareSourceB === 'current') {
            sourceBLabel = `Current page: ${pageTopic()}`;
            sourceBText = currentPageText;
        } else if (compareSourceB === 'uploaded') {
            sourceBLabel = compareSourceBDocument?.filename ? `Uploaded document: ${compareSourceBDocument.filename}` : 'Uploaded document';
            sourceBText = compareSourceBDocument?.extracted_text || '';
        } else if (fetchedWebpageUrl) {
            sourceBLabel = `Fetched webpage: ${shortDisplayUrl(fetchedWebpageUrl)}`;
        }

        if (compareAPreview) compareAPreview.textContent = comparePreviewText(sourceALabel, sourceAText);
        if (compareBPreview) compareBPreview.textContent = comparePreviewText(sourceBLabel, sourceBText);
        if (compareCompactSummary) {
            const aReady = normalizeText(sourceAText).length >= 20;
            const bReady = normalizeText(sourceBText).length >= 20;
            compareCompactSummary.textContent = `A: ${compareShortLabel(sourceALabel)} ${aReady ? 'ready' : 'needs text'} | B: ${compareShortLabel(sourceBLabel)} ${bReady ? 'ready' : 'needs text'}`;
        }

        [
            [compareAUploadBtn, compareSourceA === 'document'],
            [compareACurrentBtn, compareSourceA === 'current'],
            [compareBFetchBtn, compareSourceB === 'fetched'],
            [compareBUploadBtn, compareSourceB === 'uploaded'],
            [compareBCurrentBtn, compareSourceB === 'current'],
        ].forEach(([button, active]) => button?.classList.toggle('active', Boolean(active)));
    };

    const uploadCompareSourceBDocument = async (file) => {
        if (!file) return;
        const status = addMessage(`Uploading Source B: ${file.name}...`, 'bot', { persist: false });
        status.classList.add('typing');
        try {
            const contentBase64 = await fileToBase64(file);
            updateStatusMessage(status, 'Processing Source B document...');
            const result = await sendBackendMessage('fetchDocumentUpload', {
                filename: file.name,
                mime_type: file.type || '',
                page_url: window.location.href,
                content_base64: contentBase64
            });
            compareSourceBDocument = {
                ...result,
                extracted_text: result.extracted_text || ''
            };
            compareSourceB = 'uploaded';
            status.remove();
            addMessage(`Source B uploaded: **${result.filename}**`, 'bot', { persist: false });
            updateCompareToolPanel();
        } catch (error) {
            status.remove();
            addMessage('Source B upload failed: ' + error.message, 'bot', { persist: false });
        } finally {
            if (compareBFileInput) compareBFileInput.value = '';
        }
    };

    const resolveCompareSource = async (side, statusMessage) => {
        const source = side === 'a' ? compareSourceA : compareSourceB;
        if (side === 'a' && source === 'document') {
            const text = normalizeText(uploadedDocument?.extracted_text || '');
            return {
                text,
                label: uploadedDocument?.filename ? `Uploaded document: ${uploadedDocument.filename}` : 'Uploaded document',
                contentHash: ''
            };
        }
        if (side === 'b' && source === 'uploaded') {
            const text = normalizeText(compareSourceBDocument?.extracted_text || '');
            return {
                text,
                label: compareSourceBDocument?.filename ? `Uploaded document: ${compareSourceBDocument.filename}` : 'Uploaded document',
                contentHash: ''
            };
        }
        if (side === 'b' && source === 'fetched') {
            return {
                text: normalizeText(fetchedWebpageText || ''),
                label: fetchedWebpageUrl ? `Fetched webpage: ${shortDisplayUrl(fetchedWebpageUrl)}` : 'Fetched webpage',
                contentHash: ''
            };
        }

        updateStatusMessage(statusMessage, `Reading current page for Source ${side.toUpperCase()}...`);
        const contentHash = await prepareLivePageContent(statusMessage);
        return {
            text: normalizeText(latestContent || ''),
            label: `Current page: ${pageTopic()}`,
            contentHash
        };
    };

    const tableCell = (value, maxLength = 120) => {
        const text = String(value || '').replace(/\|/g, '\\|').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
        return text.length > maxLength ? `${text.slice(0, maxLength - 3).trim()}...` : text;
    };

    const titleCaseCompare = (value) => String(value || '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (match) => match.toUpperCase());

    const compareRowSummary = (row) => {
        const impact = titleCaseCompare(row.impact || '');
        return [
            tableCell(row.dimension, 42),
            tableCell(row.status, 24),
            tableCell(row.match_quality || 'Must Confirm', 18),
            tableCell(impact || 'Neutral', 18),
            tableCell(row.source_a_evidence, 105),
            tableCell(row.source_b_evidence, 105),
            tableCell(row.reason, 120)
        ];
    };

    const compareBulletLines = (rows, limit = 4) => rows
        .slice(0, limit)
        .map((row) => `- **${tableCell(row.dimension, 56)}:** ${tableCell(row.reason || row.status, 140)}`);

    const compareSectionTable = (rows, sectionType = 'summary', limit = 5) => {
        if (!rows.length) return '';
        const actionForRow = (row) => {
            const status = row.status || '';
            const quality = row.match_quality || '';
            if (sectionType === 'match') return 'Keep this evidence visible and measurable.';
            if (sectionType === 'extra') return row.impact === 'positive' ? 'Use as an extra strength.' : 'Mention only if relevant.';
            if (sectionType === 'risk' || status === 'Conflict' || quality === 'Must Confirm') return 'Confirm before deciding.';
            if (status === 'Partial Match') return 'Strengthen with clearer proof.';
            if (status === 'Missing From A' || status === 'Missing From B') return 'Add or verify this gap.';
            return 'Review this item.';
        };
        return [
            '| Area | Quality | Evidence | Next step |',
            '|---|---|---|---|',
            ...rows.slice(0, limit).map((row) => {
                const evidence = row.source_b_evidence && !/^not found/i.test(row.source_b_evidence)
                    ? row.source_b_evidence
                    : row.source_a_evidence;
                return `| ${tableCell(row.dimension, 46)} | ${tableCell(row.match_quality || row.status, 24)} | ${tableCell(evidence || row.reason, 110)} | ${tableCell(actionForRow(row), 80)} |`;
            })
        ].join('\n');
    };

    const compareResultMarkdown = (result) => {
        const rows = Array.isArray(result.comparison_table) ? result.comparison_table : [];
        const visibleRows = rows.slice(0, 10);
        const table = rows.length
            ? [
                '| Area | Status | Quality | Impact | Source A | Source B | Reason |',
                '|---|---|---|---|---|---|---|',
                ...visibleRows.map((row) => {
                    const cells = compareRowSummary(row);
                    return `| ${cells.join(' | ')} |`;
                })
            ].join('\n')
            : 'No comparison rows returned.';
        const count = (items) => Array.isArray(items) ? items.length : 0;
        const docTypes = result.document_types || {};
        const scoreDetails = result.score_details || {};
        const statusCounts = scoreDetails.status_counts || {};
        const impactCounts = scoreDetails.impact_counts || {};
        const matches = Array.isArray(result.matches) ? result.matches : [];
        const gaps = [
            ...(Array.isArray(result.missing_from_a) ? result.missing_from_a : []),
            ...(Array.isArray(result.missing_from_b) ? result.missing_from_b : [])
        ];
        const weakRows = [
            ...gaps,
            ...(Array.isArray(result.partial_matches) ? result.partial_matches : [])
        ];
        const conflicts = Array.isArray(result.conflicts) ? result.conflicts : [];
        const riskRows = [
            ...conflicts,
            ...rows.filter((row) => row.match_quality === 'Must Confirm' && row.status !== 'Conflict')
        ];
        const extras = Array.isArray(result.extra_strengths) ? result.extra_strengths : [];
        const resumeImprovements = result.resume_improvements || {};
        const missingKeywords = Array.isArray(resumeImprovements.missing_keywords) ? resumeImprovements.missing_keywords : [];
        const whatToAdd = Array.isArray(resumeImprovements.what_to_add) ? resumeImprovements.what_to_add : [];
        const coverLetterLine = resumeImprovements.cover_letter_line || '';
        const finalDecision = result.final_decision || '';
        const decisionReason = result.decision_reason || '';
        const decisionSection = finalDecision
            ? `#### Final decision\n**${tableCell(finalDecision, 40)}**${decisionReason ? ` - ${tableCell(decisionReason, 220)}` : ''}`
            : '';
        const resumeImprovementSection = (missingKeywords.length || whatToAdd.length || coverLetterLine)
            ? [
                '#### Resume improvements',
                missingKeywords.length ? `**Missing keywords:** ${missingKeywords.map((item) => `\`${tableCell(item, 36)}\``).join(', ')}` : '',
                whatToAdd.length ? `**What to add:**\n${whatToAdd.slice(0, 6).map((item) => `- ${tableCell(item, 150)}`).join('\n')}` : '',
                coverLetterLine ? `**Cover letter line:** ${tableCell(coverLetterLine, 220)}` : ''
            ].filter(Boolean).join('\n\n')
            : '';
        const overview = [
            '| Item | Value |',
            '|---|---|',
            `| Score | ${result.score ?? 'N/A'}/100 |`,
            `| Verdict | ${tableCell(result.verdict || 'Not available', 80)} |`,
            finalDecision ? `| Final Decision | ${tableCell(finalDecision, 60)} |` : '',
            `| Source A Type | ${tableCell(docTypes.a || 'Unknown', 60)} |`,
            `| Source B Type | ${tableCell(docTypes.b || 'Unknown', 60)} |`,
            `| Matches | ${count(result.matches)} |`,
            `| Gaps | ${count(result.missing_from_a) + count(result.missing_from_b)} |`,
            `| Conflicts | ${count(result.conflicts)} |`
        ].filter(Boolean).join('\n');
        const impactLine = Object.keys(impactCounts).length
            ? Object.entries(impactCounts).map(([key, value]) => `${titleCaseCompare(key)}: ${value}`).join(', ')
            : Object.entries(statusCounts).map(([key, value]) => `${key}: ${value}`).join(', ');

        return [
            `### Compare Report`,
            overview,
            '',
            impactLine ? `**Impact summary:** ${impactLine}` : '',
            result.warning ? `**Note:** ${result.warning}` : '',
            '',
            decisionSection,
            '',
            matches.length ? `#### Strong matches\n${compareSectionTable(matches, 'match')}` : '',
            weakRows.length ? `#### Gaps and weak areas\n${compareSectionTable(weakRows, 'gap', 6)}` : '',
            riskRows.length ? `#### Risks and confirmations\n${compareSectionTable(riskRows, 'risk', 6)}` : '',
            extras.length ? `#### Extra strengths\n${compareSectionTable(extras, 'extra', 5)}` : '',
            resumeImprovementSection,
            '',
            `#### Recommendation`,
            `> ${result.recommendation || 'Review the comparison table before deciding.'}`,
            '',
            `#### Side-by-side comparison`,
            table,
            '',
            result.answer ? `#### Explanation\n${result.answer}` : ''
        ].filter(Boolean).join('\n\n');
    };

    const runCompareTool = async (payload, streamHandlers = {}) => {
        let baseResult = null;
        let finalResult = null;
        let streamedAnswer = '';
        const doneEvent = await streamBackendCompare(payload, (event) => {
            if (event.type === 'compare_result') {
                baseResult = event.result || null;
                streamHandlers.onCompareResult?.(baseResult, event);
            } else if (event.type === 'meta') {
                streamHandlers.onMeta?.(event);
            } else if (event.type === 'delta') {
                streamedAnswer += event.text || '';
                streamHandlers.onDelta?.(streamedAnswer, event, baseResult);
            } else if (event.type === 'compare_done') {
                finalResult = event.result || null;
                streamHandlers.onDone?.(finalResult, event);
            }
            streamHandlers.onEvent?.(event);
        }, streamHandlers.requestId || '');

        const result = finalResult || doneEvent.result || (baseResult ? { ...baseResult, answer: streamedAnswer } : null);
        if (!result || !result.ok) {
            throw new Error(result?.error || 'No comparison was returned.');
        }
        if (doneEvent.type === 'compare_partial') {
            const warning = doneEvent.message || 'The structured comparison is ready, but the final explanation timed out.';
            result.warning = warning;
            result.answer = `${streamedAnswer || ''}\n\n${warning}`.trim();
            result.confidence = result.confidence || 'compare tool partial';
        }
        return result;
    };

    const renderCompareResult = async (result, meta = {}) => {
        await addBotMessageAnimated(
            compareResultMarkdown(result),
            result.sources || [],
            false,
            {
                provider: result.provider,
                model: result.model,
                confidence: result.confidence || 'compare tool',
                question: meta.question || result.compare_goal || 'Compare',
                contentHash: meta.contentHash || '',
                followUps: Array.isArray(result.suggestions) ? result.suggestions.slice(0, 3) : []
            }
        );
    };

    const collapseCompareControls = () => {
        compareAdvancedOpen = false;
        updateCompareToolPanel();
    };

    const executeComparePayload = async (payload, options = {}) => {
        const requestId = options.requestId || `compare-${Date.now()}-${++requestSerial}`;
        activeBackendRequestId = requestId;
        collapseCompareControls();
        let streamMessage = null;
        let streamedBaseResult = null;
        const removeStatus = () => {
            if (options.statusMessage?.isConnected) {
                options.statusMessage.remove();
            }
        };
        setSendButtonBusy(true);

        try {
            const result = await runCompareTool(payload, {
                requestId,
                onCompareResult: (baseResult) => {
                    streamedBaseResult = baseResult;
                    removeStatus();
                    streamMessage = createStreamingBotMessage('Writing comparison explanation...');
                    updateStreamingBotMessage(streamMessage, compareResultMarkdown({ ...baseResult, answer: 'Writing final explanation...' }));
                },
                onMeta: () => {},
                onDelta: (answer) => {
                    if (streamMessage && streamedBaseResult) {
                        updateStreamingBotMessage(streamMessage, compareResultMarkdown({ ...streamedBaseResult, answer }));
                    }
                }
            });
            removeStatus();
            const details = {
                provider: result.provider,
                model: result.model,
                confidence: result.confidence || 'compare tool',
                question: options.question || payload.compare_goal || 'Compare',
                contentHash: options.contentHash || '',
                followUps: Array.isArray(result.suggestions) ? result.suggestions.slice(0, 3) : []
            };
            if (streamMessage) {
                finalizeStreamingBotMessage(streamMessage, compareResultMarkdown(result), result.sources || [], false, details);
            } else {
                await renderCompareResult(result, details);
            }
            return result;
        } finally {
            if (activeBackendRequestId === requestId) {
                activeBackendRequestId = '';
            }
            setSendButtonBusy(false);
            updateCompareToolPanel();
            input.focus();
        }
    };

    const askCompareGoal = (payload, meta = {}) => {
        pendingCompareRequest = { payload, meta };
        clearFollowUpButtons();
        const msg = addMessage('How do you want me to compare these sources?', 'bot', { persist: false });
        const goals = ['Role fit', 'Feature comparison', 'Policy comparison', 'Pricing comparison', 'General comparison'];
        const actions = document.createElement('div');
        actions.className = 'message-followups compare-goal-actions';
        goals.forEach((goal) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = goal;
            button.onclick = async () => {
                const pending = pendingCompareRequest;
                pendingCompareRequest = null;
                clearFollowUpButtons();
                addMessage(goal, 'user');
                if (!pending) return;
                const requestId = `compare-${Date.now()}-${++requestSerial}`;
                const status = addToolStatusMessage('Compare Tool', `Comparing by ${goal}...`);
                try {
                    await executeComparePayload(
                        { ...pending.payload, compare_goal: goal },
                        { ...pending.meta, question: `${pending.meta.question || 'Compare'} (${goal})`, requestId, statusMessage: status }
                    );
                } catch (error) {
                    if (status.isConnected) status.remove();
                    addMessage('Compare Tool failed: ' + error.message, 'bot', { persist: false });
                    console.error('Compare Tool Error:', error);
                }
            };
            actions.appendChild(button);
        });
        msg.insertAdjacentElement('afterend', actions);
        scrollMessagesToBottom();
    };

    const runCompareToolFromPanel = async () => {
        if (activeDocumentMode !== 'compare') setDocumentMode('compare');
        const currentRequest = ++requestSerial;
        const compareRequestId = `compare-tool-${Date.now()}-${currentRequest}`;
        addMessage('Run Compare', 'user');
        const status = addToolStatusMessage('Compare Tool', 'Preparing sources...');
        let statusRemoved = false;
        const removeStatus = () => {
            if (statusRemoved) return;
            statusRemoved = true;
            status.remove();
        };
        setSendButtonBusy(true);

        try {
            const sourceA = await resolveCompareSource('a', status);
            const sourceB = await resolveCompareSource('b', status);
            if (!sourceA.text || sourceA.text.length < 20) {
                removeStatus();
                addMessage('Source A needs readable text. Upload a document or use the current page.', 'bot', { persist: false });
                return;
            }
            if (!sourceB.text || sourceB.text.length < 20) {
                removeStatus();
                addMessage('Source B needs readable text. Fetch a URL, upload a document, or use the current page.', 'bot', { persist: false });
                return;
            }
            updateStatusMessage(status, 'Running deterministic comparison...');
            const modelRequest = selectedModelRequest();
            const payload = {
                document_a_text: sourceA.text,
                document_a_label: sourceA.label,
                document_b_text: sourceB.text,
                document_b_label: sourceB.label,
                compare_goal: 'General comparison',
                ollama_model: modelRequest.ollama_model,
                openrouter_model: modelRequest.openrouter_model,
                force_provider: modelRequest.force_provider
            };
            removeStatus();
            askCompareGoal(payload, {
                question: 'Compare',
                contentHash: sourceA.contentHash || sourceB.contentHash || '',
                requestId: compareRequestId
            });
        } catch (error) {
            removeStatus();
            addMessage('Compare Tool failed: ' + error.message, 'bot', { persist: false });
            console.error('Compare Tool Error:', error);
        } finally {
            setSendButtonBusy(false);
            updateCompareToolPanel();
            input.focus();
        }
    };

    const handleSend = async (presetQuestion = '', options = {}) => {
        if (activeBackendRequestId && typeof presetQuestion !== 'string') {
            abortCurrentRequest();
            return;
        }

        const hasPresetQuestion = typeof presetQuestion === 'string' && presetQuestion.length > 0;
        const rawQuestion = hasPresetQuestion ? presetQuestion : input.value;
        const question = rawQuestion.trim();
        if (!question) return;

        const backendQuestion = options.revisionOf
            ? `${question}\n\nSystem: Improve the previous answer. Do not repeat it. Fix missing details, clarity, structure, and correctness using the same context.`
            : options.regenerateDiagram
            ? `${question}\n\nSystem: Regenerate with a different layout. Keep the same topic and produce a fresh JSON flowchart with different structure, grouping, orientation, or node arrangement.`
            : question;
        clearFollowUpButtons();

        const requestMode = activeDocumentMode;
        const currentRequest = ++requestSerial;
        stoppedSerial = 0;
        if (!options.skipUserEcho) {
            addMessage(options.forceProvider ? `${question} (${options.forceProvider})` : question, 'user');
        }
        if (!hasPresetQuestion) {
            input.value = '';
            input.style.height = '';
        }

        if (requestMode !== 'compare' && !options.revisionOf && !options.forceProvider && (options.forceChart || detectChartToolIntent(question))) {
            if (await runChartTool(question, options)) {
                return;
            }
        }

        const canUseWebsiteTools = !options.revisionOf && requestMode === 'website' && !options.forceProvider;
        if (canUseWebsiteTools) {
            const toolLookupStatus = addToolStatusMessage('Tool Router', 'Looking for matching tools...');
            await new Promise((resolve) => window.setTimeout(resolve, 120));

            updateStatusMessage(toolLookupStatus, 'Checking Workflow Discovery...');
            if (detectWorkflowDiscoveryIntent(question) && !options.skipWorkflow) {
                toolLookupStatus.remove();
                if (await runWorkflowDiscoveryTool(question, options)) {
                    return;
                }
            }

            updateStatusMessage(toolLookupStatus, 'Checking Flowchart Tool...');
            if (detectFlowchartToolIntent(question) || options.regenerateDiagram) {
                toolLookupStatus.remove();
                if (await runFlowchartTool(question, options)) {
                    return;
                }
            }

            updateStatusMessage(toolLookupStatus, 'Checking Page Summarizer Tool...');
            if (detectPageSummarizerToolIntent(question)) {
                toolLookupStatus.remove();
                if (await runPageSummarizerTool(question, options)) {
                    return;
                }
            }

            updateStatusMessage(toolLookupStatus, 'Checking Link Finder Tool...');
            if (detectLinkFinderToolIntent(question)) {
                toolLookupStatus.remove();
                if (handleLinkFinderTool(question)) {
                    return;
                }
            }

            toolLookupStatus.remove();
        }

        if (!options.revisionOf && requestMode === 'website' && !options.forceProvider && handleLocalPageAction(question)) {
            return;
        }

        if (['document', 'compare'].includes(requestMode) && !uploadedDocument) {
            addMessage('Upload a document first, then I can answer from it or compare it with the website.', 'bot', { persist: false });
            fileInput.click();
            return;
        }

        if (!options.revisionOf && requestMode === 'document' && !options.forceProvider && handleLocalDocumentFind(question)) {
            return;
        }

        if (!options.revisionOf && requestMode === 'compare') {
            const compareRequestId = `compare-${Date.now()}-${currentRequest}`;
            const typing = addAnswerStatusMessage('compare', 'Preparing Compare Tool...');
            typing.classList.add('typing');
            let typingRemoved = false;
            const removeTyping = () => {
                if (typingRemoved) return;
                typingRemoved = true;
                typing.remove();
            };
            setSendButtonBusy(true);

            try {
                const documentAText = normalizeText(uploadedDocument?.extracted_text || '');
                if (!documentAText || documentAText.length < 20) {
                    removeTyping();
                    addMessage('The uploaded document does not have enough readable text to compare. Try uploading a PDF, DOCX, TXT, MD, CSV, JSON, or HTML file.', 'bot', { persist: false });
                    return;
                }

                let documentBText = normalizeText(fetchedWebpageText || '');
                let documentBLabel = fetchedWebpageUrl ? `Fetched webpage: ${shortDisplayUrl(fetchedWebpageUrl)}` : `Current page: ${pageTopic()}`;
                let contentHash = '';

                if (!documentBText) {
                    updateStatusMessage(typing, 'Reading current page as Document B...');
                    contentHash = await prepareLivePageContent(typing);
                    documentBText = normalizeText(latestContent || '');
                    documentBLabel = `Current page: ${pageTopic()}`;
                }

                if (stoppedSerial === currentRequest) return;
                if (!documentBText || documentBText.length < 20) {
                    removeTyping();
                    addMessage('Compare Tool needs a second source with readable text. Fetch a webpage or use a page with more visible content.', 'bot', { persist: false });
                    return;
                }

                updateStatusMessage(typing, 'Comparing the two sources...');
                const modelRequest = selectedModelRequest();
                const payload = {
                    document_a_text: documentAText,
                    document_a_label: uploadedDocument?.filename ? `Uploaded document: ${uploadedDocument.filename}` : 'Uploaded document',
                    document_b_text: documentBText,
                    document_b_label: documentBLabel,
                    compare_goal: backendQuestion,
                    ollama_model: modelRequest.ollama_model,
                    openrouter_model: modelRequest.openrouter_model,
                    force_provider: options.forceProvider || modelRequest.force_provider
                };
                if (stoppedSerial === currentRequest) return;
                removeTyping();
                askCompareGoal(payload, {
                    question,
                    contentHash,
                    requestId: compareRequestId
                });
                return;
            } catch (error) {
                removeTyping();
                if (stoppedSerial === currentRequest || /cancelled/i.test(error.message || '')) {
                    stoppedSerial = currentRequest;
                } else {
                    addMessage('Compare Tool failed: ' + error.message, 'bot', { persist: false });
                    console.error('Compare Tool Error:', error);
                }
                return;
            } finally {
                setSendButtonBusy(false);
                input.focus();
            }
        }

        const backendRequestId = `chat-${Date.now()}-${currentRequest}`;
        activeBackendRequestId = backendRequestId;
        const typing = addAnswerStatusMessage(requestMode);
        activeResponseMessage = typing;
        typing.classList.add('typing');
        setSendButtonBusy(true);
        const memoryTurn = rememberUserTurn(question, requestMode);

        try {
            const needsWebsiteContext = requestMode !== 'document';
            const contentHash = needsWebsiteContext
                ? (activeScope === 'site' && !siteContentHash
                    ? await crawlWebsite(typing, backendRequestId)
                    : (options.contentHash || (
                        activeScope === 'page'
                            ? await prepareLivePageContent(typing)
                            : await ensureIndexed(false, typing, backendRequestId)
                    )))
                : '';
            if (stoppedSerial === currentRequest) return;
            updateStatusMessage(typing, answerGenerationStatus(requestMode, Boolean(options.allowExternalSearch)));
            const modelRequest = selectedModelRequest();
            const forceProvider = options.forceProvider || modelRequest.force_provider;
            let autofillRequested = requestMode === 'website' && !options.revisionOf && detectAutofillIntent(question);
            let workflowRequested = false;

            // ── Router: check for clarification-needed on ambiguous queries ──
            // Only runs when the query is not obviously autofill/chart/flowchart
            // (those are already handled by their own fast checks above).
            if (!autofillRequested && requestMode === 'website' && !options.revisionOf
                && !options._skipRouter) {
                const isObviousSpecial = /\b(chart|graph|flowchart|flow\s+diagram|summarize|summarise)\b/i.test(question)
                    || /\b(fill|autofill|auto-fill)\b/i.test(question);
                if (!isObviousSpecial) {
                    let routerResult;
                    try {
                        routerResult = await callIntentRouter(question, {
                            mode: requestMode,
                            forceProvider: options.forceProvider,
                        });
                    } catch (_) { /* non-fatal */ }

                    if (routerResult && routerResult.needs_clarification && routerResult.clarification_prompt) {
                        // Low confidence — show clarification instead of guessing
                        typing.remove();
                        activeResponseMessage = null;
                        addMessage(routerResult.clarification_prompt, 'bot', { persist: false });
                        return;
                    }

                    // Safety block (confidence < 0.70 for non-normal-chat intents)
                    if (routerResult && !routerResult.safety?.ok
                        && routerResult.intent !== 'normal_chat') {
                        typing.remove();
                        activeResponseMessage = null;
                        addMessage(
                            'I need more context before I can do that safely. Could you be more specific?',
                            'bot', { persist: false }
                        );
                        return;
                    }
                    if (routerResult && routerResult.intent === 'autofill_form' && routerResult.safety?.ok) {
                        autofillRequested = true;
                    }
                    
                    if (routerResult && routerResult.intent === 'workflow_steps' && routerResult.safety?.ok) {
                        workflowRequested = true;
                    }
                }
            }
            // ─────────────────────────────────────────────────────────────────
            if (workflowRequested) {
                typing.remove();
                activeResponseMessage = null;
                if (await runWorkflowDiscoveryTool(question, { ...options, forceWorkflowDiscovery: true })) {
                    return;
                }
            }
            const autofillProfile = autofillRequested ? currentUserProfile() : null;
            if (autofillRequested) {
                if (!hasProfileValues(autofillProfile)) {
                    typing.remove();
                    activeResponseMessage = null;
                    addMessage('Add your profile details in Settings > Profile first, then I can prepare an autofill plan.', 'bot', { persist: false });
                    return;
                }

                if (!options.autofillConfirmed) {
                    typing.remove();
                    activeResponseMessage = null;
                    const msgEl = addMessage('I found editable fields on this page and a saved profile.\n\nWould you like me to analyze the form and prepare an autofill plan?', 'bot', { persist: false });
                    
                    const btnContainer = document.createElement('div');
                    btnContainer.className = 'autofill-confirm-buttons action-buttons';
                    btnContainer.style.marginTop = '12px';
                    
                    const analyzeBtn = document.createElement('button');
                    analyzeBtn.textContent = 'Analyze Form';
                    analyzeBtn.className = 'action-approve';
                    analyzeBtn.onclick = () => {
                        btnContainer.remove();
                        msgEl.remove();
                        performMessageAction(question, { ...options, autofillConfirmed: true });
                    };

                    const cancelBtn = document.createElement('button');
                    cancelBtn.textContent = 'Cancel';
                    cancelBtn.className = 'action-cancel';
                    cancelBtn.onclick = () => {
                        btnContainer.remove();
                        msgEl.querySelector('.markdown-body').textContent = 'Autofill analysis cancelled.';
                    };
                    
                    btnContainer.appendChild(analyzeBtn);
                    btnContainer.appendChild(cancelBtn);
                    msgEl.appendChild(btnContainer);
                    return;
                }
            }

            const autofillInputs = autofillRequested ? scrapePageInputs() : [];
            const autofillInputsForBackend = autofillInputs.map(({ field_id, ...field }) => field);
            if (autofillRequested) {
                if (!autofillInputs.length) {
                    typing.remove();
                    activeResponseMessage = null;
                    addMessage("I couldn't find visible, editable form fields on this page.", 'bot', { persist: false });
                    return;
                }
                updateStatusMessage(typing, `Analyzing ${autofillInputs.length} form field${autofillInputs.length === 1 ? '' : 's'}...`);
            }

            // Search mode selector — show Quick vs Deep choice for website mode
            if (
                requestMode === 'website' &&
                !options.searchMode &&
                !options.revisionOf &&
                !options.skipSearchChoice &&
                !options.forceProvider &&
                !workflowRequested &&
                !detectWorkflowDiscoveryIntent(question) &&
                !detectFlowchartToolIntent(question) &&
                !detectChartToolIntent(question) &&
                !detectPageSummarizerToolIntent(question) &&
                !detectLinkFinderToolIntent(question)
            ) {
                setSendButtonBusy(false);
                await showSearchModeCard(question, options);
                return;
            }

            const chatPayload = {
                url: activeScopeUrl,
                question: backendQuestion,
                request_id: backendRequestId,
                content: needsWebsiteContext && activeScope === 'page' ? latestContent : '',
                content_hash: contentHash,
                ollama_model: modelRequest.ollama_model || '',
                openrouter_model: modelRequest.openrouter_model || '',
                gemini_model: modelRequest.gemini_model || '',
                force_provider: forceProvider,
                allow_external_search: Boolean(options.allowExternalSearch),
                concise_answer: conciseInput.checked,
                document_id: uploadedDocument?.document_id || '',
                document_mode: requestMode,
                fetched_webpage_text: (requestMode === 'compare' && fetchedWebpageText) ? fetchedWebpageText : '',
                fetched_webpage_url: (requestMode === 'compare' && fetchedWebpageUrl) ? fetchedWebpageUrl : '',
                conversation_memory: conversationMemorySnapshot(requestMode),
                revision_of: options.revisionOf || null,
                deep_search: Boolean(options.forceDeepContext),
                history: modeScopedHistory(requestMode)
            };
            if (autofillRequested) {
                chatPayload.profile = autofillProfile;
                chatPayload.page_inputs = autofillInputsForBackend;
            }
            const STREAMABLE_MODES = new Set(['website', 'document']);
            let shouldStream = STREAMABLE_MODES.has(requestMode) && !autofillRequested;

            let response;
            if (shouldStream) {
                typing.remove();
                const streamMessage = createStreamingBotMessage(answerGenerationStatus(requestMode, Boolean(options.allowExternalSearch)));
                activeResponseMessage = streamMessage;
                let streamedAnswer = '';
                const streamState = {
                    provider: '',
                    model: '',
                    confidence: '',
                    sources: [],
                    suggestions: [],
                    usedExternalSearch: false,
                    deepSearchSummary: null
                };

                try {
                    response = await streamBackendChat(chatPayload, (event) => {
                        if (stoppedSerial === currentRequest) return;
                        if (event.type === 'context') {
                            streamState.sources = event.sources || [];
                            streamState.confidence = event.confidence || '';
                            streamState.usedExternalSearch = Boolean(event.used_external_search);
                            updateStatusMessage(
                                streamMessage,
                                streamState.usedExternalSearch
                                    ? 'Using approved web results with page context...'
                                    : 'Found relevant page context. Preparing the answer...'
                            );
                        } else if (event.type === 'deep_search_summary') {
                            streamState.deepSearchSummary = event;
                            updateStatusMessage(streamMessage, 'Deep Search Complete. Generating final answer...');
                        } else if (event.type === 'meta') {
                            streamState.provider = event.provider || streamState.provider;
                            streamState.model = event.model || streamState.model;
                            updateStatusMessage(streamMessage, 'Writing the answer...');
                        } else if (event.type === 'delta') {
                            streamedAnswer += event.text || '';
                            updateStreamingBotMessage(streamMessage, streamedAnswer);
                        } else if (event.type === 'done') {
                            streamState.provider = event.provider || streamState.provider;
                            streamState.model = event.model || streamState.model;
                            streamState.sources = event.sources || streamState.sources;
                            streamState.suggestions = event.suggestions || [];
                            streamState.usedExternalSearch = Boolean(event.used_external_search);
                            streamState.confidence = event.confidence || streamState.confidence;
                        }
                    });
                } catch (streamError) {
                    if (streamedAnswer) {
                        // Partial content already received — finalize what we have instead of discarding.
                        console.warn('Streaming ended early, but partial content received. Finalizing.', streamError);
                        response = {
                            answer: streamedAnswer,
                            sources: streamState.sources,
                            suggestions: streamState.suggestions,
                            used_external_search: streamState.usedExternalSearch,
                            provider: streamState.provider,
                            model: streamState.model,
                            confidence: streamState.confidence,
                            _partialStream: true
                        };
                    } else {
                        // No content at all — fall back to standard (non-streaming) endpoint.
                        console.warn('Streaming chat failed with no content; retrying with standard chat.', streamError);
                        streamMessage.remove();
                        activeResponseMessage = null;
                        shouldStream = false;
                        const fallbackStatus = addAnswerStatusMessage(requestMode, 'Streaming had trouble. Trying a standard response...');
                        fallbackStatus.classList.add('typing');
                        response = await sendBackendMessage('fetchChat', chatPayload);
                        fallbackStatus.remove();
                        if (stoppedSerial === currentRequest) return;
                    }
                }

                if (response.requires_external_permission) {
                    streamMessage.remove();
                } else if (streamedAnswer) {
                    finalizeStreamingBotMessage(
                        streamMessage,
                        streamedAnswer,
                        streamState.sources,
                        streamState.usedExternalSearch,
                        {
                            provider: response.provider || streamState.provider,
                            model: response.model || streamState.model,
                            confidence: response.confidence || streamState.confidence,
                            question,
                            contentHash,
                            memoryTurn,
                            followUps: pageSpecificSuggestions(response.suggestions || streamState.suggestions, 3),
                            deepSearchSummary: streamState.deepSearchSummary
                        }
                    );
                    activeResponseMessage = null;
                    response = {
                        ...response,
                        answer: streamedAnswer,
                        sources: streamState.sources,
                        suggestions: response.suggestions || streamState.suggestions,
                        used_external_search: streamState.usedExternalSearch,
                        provider: response.provider || streamState.provider,
                        model: response.model || streamState.model,
                        confidence: response.confidence || streamState.confidence
                    };
                }
            } else {
                response = await sendBackendMessage('fetchChat', chatPayload);
                if (stoppedSerial === currentRequest) return;

                if (response.requires_index) {
                    const freshHash = await ensureIndexed(true, typing, backendRequestId);
                    if (stoppedSerial === currentRequest) return;
                    updateStatusMessage(typing, 'Page index is ready. Preparing the answer...');
                    response = await sendBackendMessage('fetchChat', {
                        ...chatPayload,
                        content_hash: freshHash,
                        content: needsWebsiteContext && activeScope === 'page' ? latestContent : ''
                    });
                }
                if (stoppedSerial === currentRequest) return;
                typing.remove();
                activeResponseMessage = null;
            }

            if (response && response.requires_external_permission) {
                addExternalSearchReviewCard({
                    question,
                    onApprove: () => handleSend(question, {
                        ...options,
                        allowExternalSearch: true,
                        contentHash,
                        skipUserEcho: true
                    })
                });
                setFollowUps(pageSpecificSuggestions([], 3));
                return;
            }

            if (response && response.answer && !shouldStream) {
                const dynamicSuggestions = pageSpecificSuggestions(response.suggestions, 3);
                await addBotMessageAnimated(
                    response.answer,
                    response.sources || [],
                    response.used_external_search,
                    {
                        provider: response.provider,
                        model: response.model,
                        confidence: response.confidence,
                        question,
                        contentHash,
                        memoryTurn,
                        followUps: dynamicSuggestions
                    }
                );
            } else if (response && response.answer && shouldStream) {
                // Streaming follow-ups are appended to the streamed message when it finalizes.
            } else {
                addMessage("Error: Received no response from backend.", 'bot');
            }
        } catch (error) {
            typing.remove();
            if (stoppedSerial === currentRequest || /cancelled/i.test(error.message || '')) {
                stoppedSerial = currentRequest;
            } else {
                addMessage("I couldn't reach the backend. Please ensure the server is running and reload the page. Details: " + error.message, 'bot');
                console.error("Chatbot Error:", error);
            }
        } finally {
            if (stoppedSerial === currentRequest) {
                if (activeResponseMessage) activeResponseMessage.remove();
                typing.remove();
            }
            if (activeBackendRequestId === backendRequestId) {
                activeBackendRequestId = '';
            }
            setSendButtonBusy(false);
            input.focus();
        }
    };

    const regenerateFlowDiagram = (diagramWrap) => {
        const question = diagramWrap?.dataset.originalQuestion || '';
        if (!question.trim()) {
            addMessage('I can regenerate new diagrams from this session, but this older diagram does not have its original question saved.', 'bot', { persist: false });
            return;
        }

        handleSend(question, {
            regenerateDiagram: true,
            skipUserEcho: true
        });
    };

    const showAutofillSessionReminder = () => {
        const session = loadAutofillSession();
        if (!session || session.phase !== 'filled') return;
        const sameUrl = session.url === window.location.href;
        const fields = Array.isArray(session.actions) ? session.actions.length : 0;
        if (!fields) return;
        addMessage(
            sameUrl
                ? `Autofill session is active for this form. ${fields} mapping${fields === 1 ? '' : 's'} were used on this page.`
                : 'Autofill session is active. If this is the next step, ask me to autofill this page and I will analyze the new fields.',
            'bot',
            { persist: false }
        );
    };

    // Events
    if (scrollDownBtn) {
        scrollDownBtn.onclick = (event) => {
            event.preventDefault();
            scrollMessagesToBottom(true);
        };
    }

    messagesContainer.addEventListener('scroll', updateScrollDownButton);

    messagesContainer.addEventListener('click', (event) => {
        // Don't intercept clicks on actual links — let them navigate normally
        const clickedLink = event.target.closest('a[href]');
        if (clickedLink) return;

        const tableWrap = event.target.closest('.message-table-wrap');
        if (tableWrap) {
            event.preventDefault();
            openTableModal(tableWrap);
            return;
        }
        const regenerateButton = event.target.closest('.flow-diagram-regenerate');
        if (regenerateButton) {
            event.preventDefault();
            event.stopPropagation();
            regenerateFlowDiagram(regenerateButton.closest('.flow-diagram-wrap'));
            return;
        }
        // Chart SVG/PNG download buttons
        const chartSvgBtn = event.target.closest('.chart-download-svg');
        if (chartSvgBtn) { event.stopPropagation(); downloadChartSvg(chartSvgBtn.closest('.chart-wrap')); return; }
        const chartPngBtn = event.target.closest('.chart-download-png');
        if (chartPngBtn) { event.stopPropagation(); downloadChartPng(chartPngBtn.closest('.chart-wrap')); return; }
        const pngButton = event.target.closest('.flow-diagram-download-png');
        if (pngButton) {
            event.preventDefault();
            event.stopPropagation();
            downloadFlowDiagramPng(pngButton.closest('.flow-diagram-wrap'));
            return;
        }
        const downloadButton = event.target.closest('.flow-diagram-download');
        if (downloadButton) {
            event.preventDefault();
            event.stopPropagation();
            downloadFlowDiagram(downloadButton.closest('.flow-diagram-wrap'));
            return;
        }
        if (event.target.closest('.flow-diagram-code')) return;
        const diagram = event.target.closest('.flow-diagram-wrap');
        if (diagram) {
            openFlowDiagramModal(diagram);
        }
    });

    messagesContainer.addEventListener('keydown', (event) => {
        if (!['Enter', ' '].includes(event.key)) return;
        const regenerateButton = event.target.closest('.flow-diagram-regenerate');
        if (regenerateButton) {
            event.preventDefault();
            regenerateFlowDiagram(regenerateButton.closest('.flow-diagram-wrap'));
            return;
        }
        const pngButton = event.target.closest('.flow-diagram-download-png');
        if (pngButton) {
            event.preventDefault();
            downloadFlowDiagramPng(pngButton.closest('.flow-diagram-wrap'));
            return;
        }
        const downloadButton = event.target.closest('.flow-diagram-download');
        if (downloadButton) {
            event.preventDefault();
            downloadFlowDiagram(downloadButton.closest('.flow-diagram-wrap'));
            return;
        }
        if (event.target.closest('.flow-diagram-code')) return;
        const tableWrap = event.target.closest('.message-table-wrap');
        if (tableWrap) {
            event.preventDefault();
            openTableModal(tableWrap);
            return;
        }
        const diagram = event.target.closest('.flow-diagram-wrap');
        if (diagram) {
            event.preventDefault();
            openFlowDiagramModal(diagram);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeFlowDiagramModal();
            closeTableModal();
        }
    });

    // Wire new toolbar mode tabs
    const modeTabsEl = document.getElementById('cb-mode-tabs');
    if (modeTabsEl) {
        modeTabsEl.onclick = (e) => {
            const tab = e.target.closest('.cb-mode-tab');
            if (!tab) return;
            const mode = tab.dataset.mode;
            if (!mode) return;
            requestDocumentMode(mode, { announce: true });
        };
    }

    // Wire inline crawl button in toolbar
    const crawlInlineBtn = document.getElementById('web-chatbot-crawl-inline');
    if (crawlInlineBtn) {
        crawlInlineBtn.onclick = () => crawlBtn.click();
    }
    const chartInlineBtn = document.getElementById('web-chatbot-chart-inline');
    if (chartInlineBtn) {
        chartInlineBtn.onclick = () => {
            const prompt = (input.value || '').trim() || defaultChartPrompt();
            handleSend(prompt, { forceChart: true });
        };
    }

    // ── Chart tool ────────────────────────────────────────────────────────────

    const CHART_COLORS = [
        '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
    ];
    const CHART_COLORS_LIGHT = [
        'rgba(37,99,235,0.15)', 'rgba(16,185,129,0.15)', 'rgba(245,158,11,0.15)',
        'rgba(239,68,68,0.15)', 'rgba(139,92,246,0.15)', 'rgba(6,182,212,0.15)',
        'rgba(249,115,22,0.15)', 'rgba(132,204,22,0.15)', 'rgba(236,72,153,0.15)', 'rgba(99,102,241,0.15)'
    ];

    const escapeChartText = (s) => String(s || '').replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]));

    const wrapChartLabel = (label, maxLen = 12) => {
        const words = String(label).split(' ');
        const lines = [];
        let cur = '';
        words.forEach(w => {
            if ((cur + ' ' + w).trim().length > maxLen && cur) { lines.push(cur.trim()); cur = w; }
            else { cur = (cur + ' ' + w).trim(); }
        });
        if (cur) lines.push(cur.trim());
        return lines.slice(0, 3);
    };

    const renderBarChart = (data, svgW, svgH, horizontal = false) => {
        const labels = data.labels;
        const datasets = data.datasets;
        const padL = horizontal ? 120 : 44, padR = 20, padT = 36, padB = horizontal ? 40 : 60;
        const chartW = svgW - padL - padR;
        const chartH = svgH - padT - padB;
        const allVals = datasets.flatMap(d => d.data);
        const maxVal = Math.max(...allVals, 1);
        const niceMax = Math.ceil(maxVal / 10) * 10 || 10;
        const groupCount = labels.length;
        const dsCount = datasets.length;
        const groupW = horizontal ? chartH / groupCount : chartW / groupCount;
        const barW = Math.max(4, (groupW * 0.7) / dsCount);
        const gridLines = 5;

        let gridSvg = '', barsSvg = '', labelsSvg = '', axisSvg = '';

        // Grid lines & axis ticks
        for (let i = 0; i <= gridLines; i++) {
            const val = Math.round((niceMax * i) / gridLines);
            if (horizontal) {
                const x = padL + (val / niceMax) * chartW;
                gridSvg += `<line x1="${x}" y1="${padT}" x2="${x}" y2="${padT + chartH}" stroke="var(--cb-border)" stroke-width="1" stroke-dasharray="3 3"/>`;
                axisSvg += `<text x="${x}" y="${padT + chartH + 16}" text-anchor="middle" class="chart-axis-label">${val}</text>`;
            } else {
                const y = padT + chartH - (val / niceMax) * chartH;
                gridSvg += `<line x1="${padL}" y1="${y}" x2="${padL + chartW}" y2="${y}" stroke="var(--cb-border)" stroke-width="1" stroke-dasharray="3 3"/>`;
                axisSvg += `<text x="${padL - 6}" y="${y + 4}" text-anchor="end" class="chart-axis-label">${val}</text>`;
            }
        }

        // Bars and labels
        labels.forEach((label, gi) => {
            const lines = wrapChartLabel(label, horizontal ? 14 : 10);
            datasets.forEach((ds, di) => {
                const val = ds.data[gi] || 0;
                const color = CHART_COLORS[di % CHART_COLORS.length];
                const lightColor = CHART_COLORS_LIGHT[di % CHART_COLORS_LIGHT.length];
                if (horizontal) {
                    const y = padT + gi * groupW + di * barW + groupW * 0.15;
                    const w = (val / niceMax) * chartW;
                    barsSvg += `<rect x="${padL}" y="${y}" width="${w}" height="${barW - 2}" rx="3" fill="${color}" opacity="0.85"/>`;
                    if (w > 24) barsSvg += `<text x="${padL + w - 4}" y="${y + barW / 2 + 4}" text-anchor="end" class="chart-bar-label">${val}</text>`;
                    // label on left
                    if (di === 0) {
                        lines.forEach((line, li) => {
                            labelsSvg += `<text x="${padL - 6}" y="${y + barW / 2 + (li - (lines.length - 1) / 2) * 13}" text-anchor="end" class="chart-axis-label">${escapeChartText(line)}</text>`;
                        });
                    }
                } else {
                    const x = padL + gi * groupW + di * barW + groupW * 0.15;
                    const h = (val / niceMax) * chartH;
                    const y = padT + chartH - h;
                    barsSvg += `<rect x="${x}" y="${y}" width="${barW - 2}" height="${h}" rx="3" fill="${color}" opacity="0.85"/>`;
                    if (h > 18) barsSvg += `<text x="${x + barW / 2 - 1}" y="${y - 4}" text-anchor="middle" class="chart-bar-label">${val}</text>`;
                    // labels below
                    if (di === 0) {
                        const lx = padL + gi * groupW + groupW / 2;
                        lines.forEach((line, li) => {
                            labelsSvg += `<text x="${lx}" y="${padT + chartH + 16 + li * 13}" text-anchor="middle" class="chart-axis-label">${escapeChartText(line)}</text>`;
                        });
                    }
                }
            });
        });

        // Legend
        let legendSvg = '';
        if (datasets.length > 1) {
            datasets.forEach((ds, di) => {
                const lx = padL + di * 120;
                const ly = 14;
                legendSvg += `<rect x="${lx}" y="${ly - 9}" width="12" height="12" rx="2" fill="${CHART_COLORS[di % CHART_COLORS.length]}"/>`;
                legendSvg += `<text x="${lx + 16}" y="${ly}" class="chart-legend-label">${escapeChartText(ds.label)}</text>`;
            });
        }

        return `${gridSvg}${barsSvg}${labelsSvg}${axisSvg}${legendSvg}`;
    };

    const renderLineChart = (data, svgW, svgH) => {
        const labels = data.labels;
        const datasets = data.datasets;
        const padL = 48, padR = 20, padT = 36, padB = 54;
        const chartW = svgW - padL - padR;
        const chartH = svgH - padT - padB;
        const allVals = datasets.flatMap(d => d.data);
        const maxVal = Math.max(...allVals, 1);
        const niceMax = Math.ceil(maxVal / 10) * 10 || 10;
        const xStep = chartW / Math.max(labels.length - 1, 1);
        const gridLines = 5;
        let out = '';

        // Grid
        for (let i = 0; i <= gridLines; i++) {
            const val = Math.round((niceMax * i) / gridLines);
            const y = padT + chartH - (val / niceMax) * chartH;
            out += `<line x1="${padL}" y1="${y}" x2="${padL + chartW}" y2="${y}" stroke="var(--cb-border)" stroke-width="1" stroke-dasharray="3 3"/>`;
            out += `<text x="${padL - 6}" y="${y + 4}" text-anchor="end" class="chart-axis-label">${val}</text>`;
        }

        // Lines and dots
        datasets.forEach((ds, di) => {
            const color = CHART_COLORS[di % CHART_COLORS.length];
            const pts = ds.data.map((v, i) => ({ x: padL + i * xStep, y: padT + chartH - (v / niceMax) * chartH }));
            // Area fill
            const areaPath = `M${pts[0].x},${padT + chartH} ` + pts.map(p => `L${p.x},${p.y}`).join(' ') + ` L${pts[pts.length-1].x},${padT + chartH} Z`;
            out += `<path d="${areaPath}" fill="${color}" opacity="0.08"/>`;
            // Line
            const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
            out += `<path d="${linePath}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`;
            // Dots
            pts.forEach(p => { out += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="${color}" stroke="#fff" stroke-width="1.5"/>`; });
        });

        // X labels
        labels.forEach((label, i) => {
            const x = padL + i * xStep;
            const lines = wrapChartLabel(label, 9);
            lines.forEach((line, li) => {
                out += `<text x="${x.toFixed(1)}" y="${padT + chartH + 16 + li * 13}" text-anchor="middle" class="chart-axis-label">${escapeChartText(line)}</text>`;
            });
        });

        // Legend
        if (datasets.length > 1) {
            datasets.forEach((ds, di) => {
                out += `<rect x="${padL + di * 120}" y="5" width="12" height="3" rx="1" fill="${CHART_COLORS[di % CHART_COLORS.length]}"/>`;
                out += `<text x="${padL + di * 120 + 16}" y="14" class="chart-legend-label">${escapeChartText(ds.label)}</text>`;
            });
        }
        return out;
    };

    const renderPieDonut = (data, svgW, svgH, donut = false) => {
        const cx = svgW / 2, cy = svgH / 2;
        const r = Math.min(cx, cy) - 40;
        const innerR = donut ? r * 0.52 : 0;
        const values = data.datasets[0].data;
        const total = values.reduce((a, b) => a + b, 0) || 1;
        let angle = -Math.PI / 2;
        let slices = '', labels = '';

        values.forEach((val, i) => {
            const slice = (val / total) * 2 * Math.PI;
            const mid = angle + slice / 2;
            const x1 = cx + r * Math.cos(angle), y1 = cy + r * Math.sin(angle);
            const x2 = cx + r * Math.cos(angle + slice), y2 = cy + r * Math.sin(angle + slice);
            const ix1 = cx + innerR * Math.cos(angle), iy1 = cy + innerR * Math.sin(angle);
            const ix2 = cx + innerR * Math.cos(angle + slice), iy2 = cy + innerR * Math.sin(angle + slice);
            const large = slice > Math.PI ? 1 : 0;
            const color = CHART_COLORS[i % CHART_COLORS.length];
            const path = donut
                ? `M${x1.toFixed(1)},${y1.toFixed(1)} A${r},${r} 0 ${large},1 ${x2.toFixed(1)},${y2.toFixed(1)} L${ix2.toFixed(1)},${iy2.toFixed(1)} A${innerR},${innerR} 0 ${large},0 ${ix1.toFixed(1)},${iy1.toFixed(1)} Z`
                : `M${cx},${cy} L${x1.toFixed(1)},${y1.toFixed(1)} A${r},${r} 0 ${large},1 ${x2.toFixed(1)},${y2.toFixed(1)} Z`;
            slices += `<path d="${path}" fill="${color}" opacity="0.88" stroke="#fff" stroke-width="2"/>`;
            // label line + text
            if (val / total > 0.04) {
                const lx = cx + (r + 18) * Math.cos(mid), ly = cy + (r + 18) * Math.sin(mid);
                const tx = cx + (r + 28) * Math.cos(mid), ty = cy + (r + 28) * Math.sin(mid);
                const anchor = Math.cos(mid) > 0 ? 'start' : 'end';
                labels += `<line x1="${(cx + r * 0.9 * Math.cos(mid)).toFixed(1)}" y1="${(cy + r * 0.9 * Math.sin(mid)).toFixed(1)}" x2="${lx.toFixed(1)}" y2="${ly.toFixed(1)}" stroke="var(--cb-text-muted)" stroke-width="1"/>`;
                labels += `<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" text-anchor="${anchor}" class="chart-pie-label">${escapeChartText(data.labels[i])} (${Math.round(val/total*100)}%)</text>`;
            }
            angle += slice;
        });

        // Center text for donut
        let center = '';
        if (donut) {
            center = `<text x="${cx}" y="${cy - 6}" text-anchor="middle" class="chart-donut-center-title">${escapeChartText(data.title || '')}</text>`;
            center += `<text x="${cx}" y="${cy + 14}" text-anchor="middle" class="chart-donut-center-sub">${total}</text>`;
        }

        return `${slices}${labels}${center}`;
    };

    const renderRadarChart = (data, svgW, svgH) => {
        const cx = svgW / 2, cy = svgH / 2;
        const r = Math.min(cx, cy) - 44;
        const labels = data.labels;
        const N = labels.length;
        const datasets = data.datasets;
        const allVals = datasets.flatMap(d => d.data);
        const maxVal = Math.max(...allVals, 1);
        const niceMax = Math.ceil(maxVal / 10) * 10 || 100;
        const rings = 4;
        let out = '';

        // Rings
        for (let ring = 1; ring <= rings; ring++) {
            const rr = (ring / rings) * r;
            const pts = Array.from({ length: N }, (_, i) => {
                const a = (i / N) * 2 * Math.PI - Math.PI / 2;
                return `${(cx + rr * Math.cos(a)).toFixed(1)},${(cy + rr * Math.sin(a)).toFixed(1)}`;
            }).join(' ');
            out += `<polygon points="${pts}" fill="none" stroke="var(--cb-border)" stroke-width="1"/>`;
            out += `<text x="${cx + 4}" y="${cy - rr + 4}" class="chart-axis-label">${Math.round((ring / rings) * niceMax)}</text>`;
        }

        // Spokes and labels
        labels.forEach((label, i) => {
            const a = (i / N) * 2 * Math.PI - Math.PI / 2;
            const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
            out += `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="var(--cb-border)" stroke-width="1"/>`;
            const lx = cx + (r + 18) * Math.cos(a), ly = cy + (r + 18) * Math.sin(a);
            const anchor = Math.abs(Math.cos(a)) < 0.1 ? 'middle' : (Math.cos(a) > 0 ? 'start' : 'end');
            const lines = wrapChartLabel(label, 10);
            lines.forEach((line, li) => {
                out += `<text x="${lx.toFixed(1)}" y="${(ly + li * 13 - (lines.length - 1) * 6).toFixed(1)}" text-anchor="${anchor}" class="chart-axis-label">${escapeChartText(line)}</text>`;
            });
        });

        // Dataset polygons
        datasets.forEach((ds, di) => {
            const color = CHART_COLORS[di % CHART_COLORS.length];
            const pts = ds.data.map((v, i) => {
                const a = (i / N) * 2 * Math.PI - Math.PI / 2;
                const rv = (Math.min(v, niceMax) / niceMax) * r;
                return `${(cx + rv * Math.cos(a)).toFixed(1)},${(cy + rv * Math.sin(a)).toFixed(1)}`;
            }).join(' ');
            out += `<polygon points="${pts}" fill="${color}" fill-opacity="0.15" stroke="${color}" stroke-width="2"/>`;
            ds.data.forEach((v, i) => {
                const a = (i / N) * 2 * Math.PI - Math.PI / 2;
                const rv = (Math.min(v, niceMax) / niceMax) * r;
                out += `<circle cx="${(cx + rv * Math.cos(a)).toFixed(1)}" cy="${(cy + rv * Math.sin(a)).toFixed(1)}" r="4" fill="${color}" stroke="#fff" stroke-width="1.5"/>`;
            });
        });

        // Legend
        if (datasets.length > 1) {
            datasets.forEach((ds, di) => {
                out += `<rect x="${8 + di * 110}" y="5" width="12" height="12" rx="2" fill="${CHART_COLORS[di % CHART_COLORS.length]}"/>`;
                out += `<text x="${24 + di * 110}" y="15" class="chart-legend-label">${escapeChartText(ds.label)}</text>`;
            });
        }
        return out;
    };

    const buildChartSvg = (parsed) => {
        const type = (parsed.type || 'bar').toLowerCase();
        const svgW = 420, svgH = type === 'radar' ? 320 : (type === 'pie' || type === 'donut' ? 300 : 280);
        let inner = '';
        if (type === 'bar')            inner = renderBarChart(parsed, svgW, svgH, false);
        else if (type === 'horizontal_bar') inner = renderBarChart(parsed, svgW, svgH, true);
        else if (type === 'line')      inner = renderLineChart(parsed, svgW, svgH);
        else if (type === 'pie')       inner = renderPieDonut(parsed, svgW, svgH, false);
        else if (type === 'donut')     inner = renderPieDonut(parsed, svgW, svgH, true);
        else if (type === 'radar')     inner = renderRadarChart(parsed, svgW, svgH);
        else                           inner = renderBarChart(parsed, svgW, svgH, false);

        const title = escapeChartText(parsed.title || '');
        return `<svg viewBox="0 0 ${svgW} ${svgH}" xmlns="http://www.w3.org/2000/svg" class="chart-svg">
            <style>
                .chart-axis-label { font:11px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-muted,#64748b); }
                .chart-bar-label  { font:10px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-muted,#64748b); }
                .chart-pie-label  { font:10.5px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-main,#0f172a); }
                .chart-legend-label { font:11px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-muted,#64748b); }
                .chart-title      { font:600 13px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-main,#0f172a); }
                .chart-donut-center-title { font:600 11px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-muted,#64748b); }
                .chart-donut-center-sub   { font:700 18px var(--cb-font-sans,Inter,sans-serif); fill:var(--cb-text-main,#0f172a); }
            </style>
            ${title ? `<text x="${svgW/2}" y="18" text-anchor="middle" class="chart-title">${title}</text>` : ''}
            ${inner}
        </svg>`;
    };

    const parseChartBlock = (code) => {
        try {
            const raw = String(code || '').trim();
            const parsed = JSON.parse(raw);
            if (!parsed || !parsed.type || !Array.isArray(parsed.labels) || !Array.isArray(parsed.datasets)) return null;
            return parsed;
        } catch { return null; }
    };

    const renderChartBlock = (code) => {
        const parsed = parseChartBlock(code);
        if (!parsed) return `<pre class="message-code" data-language="chart"><code>${escapeHtml(code)}</code></pre>`;
        const svg = buildChartSvg(parsed);
        const summary = parsed.summary ? `<p class="chart-summary">${escapeHtml(parsed.summary)}</p>` : '';
        return `<div class="chart-wrap">
            ${svg}
            ${summary}
            <div class="chart-actions">
                <button type="button" class="chart-download-svg" title="Download as SVG">SVG</button>
                <button type="button" class="chart-download-png" title="Download as PNG">PNG</button>
            </div>
        </div>`;
    };

    const downloadChartSvg = (chartWrap) => {
        const svgEl = chartWrap.querySelector('svg');
        if (!svgEl) return;
        const clone = svgEl.cloneNode(true);
        const styleEl = clone.querySelector('style');
        if (styleEl) {
            styleEl.textContent = styleEl.textContent
                .replace(/var\(--cb-font-sans,[^)]+\)/g, 'Inter,sans-serif')
                .replace(/var\(--cb-text-muted,[^)]+\)/g, '#64748b')
                .replace(/var\(--cb-text-main,[^)]+\)/g, '#0f172a')
                .replace(/var\(--cb-border,[^)]+\)/g, '#e2e8f0');
        }
        const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' });
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
        a.download = 'chart.svg'; a.click(); URL.revokeObjectURL(a.href);
    };

    const downloadChartPng = async (chartWrap) => {
        const svgEl = chartWrap.querySelector('svg');
        if (!svgEl) return;
        const clone = svgEl.cloneNode(true);
        const styleEl = clone.querySelector('style');
        if (styleEl) {
            styleEl.textContent = styleEl.textContent
                .replace(/var\(--cb-font-sans,[^)]+\)/g, 'Inter,sans-serif')
                .replace(/var\(--cb-text-muted,[^)]+\)/g, '#64748b')
                .replace(/var\(--cb-text-main,[^)]+\)/g, '#0f172a')
                .replace(/var\(--cb-border,[^)]+\)/g, '#e2e8f0');
        }
        const svgStr = new XMLSerializer().serializeToString(clone);
        const vb = svgEl.viewBox.baseVal;
        const scale = 2;
        const canvas = document.createElement('canvas');
        canvas.width = (vb.width || 420) * scale; canvas.height = (vb.height || 280) * scale;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
        const img = new Image();
        const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgStr);
        await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url; });
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const a = document.createElement('a'); a.href = canvas.toDataURL('image/png');
        a.download = 'chart.png'; a.click();
    };

    // ── end chart tool ─────────────────────────────────────────────────────────

    const resizeInput = () => {
        input.style.height = '';
    };
    input.oninput = resizeInput;
    sendBtn.onclick = () => {
        if (sendBtn.classList.contains('is-stopping')) {
            abortCurrentRequest();
        } else {
            handleSend();
        }
    };
    input.onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };
    scopeSelect.onchange = () => {
        setScope(scopeSelect.value);
        saveSettings();
        if (scopeSelect.value === 'site' && !siteContentHash) {
            addMessage('Click the Globe icon to crawl the website first.', 'bot', { persist: false });
        }
    };
    sourceModeSelect.onchange = () => {
        requestDocumentMode(sourceModeSelect.value);
    };
    if (modeSelect) {
        modeSelect.onchange = () => {
            requestDocumentMode(modeSelect.value, { announce: true });
        };
    }
    if (modelSelect) {
        modelSelect.onchange = () => {
            syncModelPicker();
            saveSettings();
        };
    }
    if (modelButton && modelMenu) {
        const closeModelMenu = () => {
            modelMenu.classList.add('hidden');
            modelButton.setAttribute('aria-expanded', 'false');
        };
        const openModelMenu = () => {
            if (modeMenu && modeButton) {
                modeMenu.classList.add('hidden');
                modeButton.setAttribute('aria-expanded', 'false');
            }
            const rect = modelButton.getBoundingClientRect();
            modelMenu.style.top = 'auto';
            modelMenu.style.bottom = `${Math.max(8, window.innerHeight - rect.top + 8)}px`;
            modelMenu.style.right = `${Math.max(8, window.innerWidth - rect.right)}px`;
            modelMenu.classList.remove('hidden');
            modelButton.setAttribute('aria-expanded', 'true');
        };

        modelButton.onclick = (event) => {
            event.stopPropagation();
            if (modelMenu.classList.contains('hidden')) {
                openModelMenu();
            } else {
                closeModelMenu();
            }
        };
        modelMenu.onclick = (event) => {
            const option = event.target.closest('.model-picker-option');
            if (!option || !option.dataset.value) return;
            modelSelect.value = option.dataset.value;
            syncModelPicker();
            saveSettings();
            closeModelMenu();
        };
        document.addEventListener('click', (event) => {
            if (modelPicker && modelPicker.contains(event.target)) return;
            closeModelMenu();
        });
    }
    if (modeButton && modeMenu) {
        modeButton.onclick = (event) => {
            event.stopPropagation();
            const isOpen = !modeMenu.classList.contains('hidden');
            if (isOpen) {
                modeMenu.classList.add('hidden');
                modeButton.setAttribute('aria-expanded', 'false');
            } else {
                const rect = modeButton.getBoundingClientRect();
                modeMenu.style.top = `${rect.bottom + 9}px`;
                modeMenu.style.right = `${Math.max(8, window.innerWidth - rect.right)}px`;
                modeMenu.classList.remove('hidden');
                modeButton.setAttribute('aria-expanded', 'true');
            }
        };
        modeMenu.onclick = (event) => {
            const option = event.target.closest('.mode-picker-option');
            if (!option) return;
            requestDocumentMode(option.dataset.mode, { announce: true });
            modeMenu.classList.add('hidden');
            modeButton.setAttribute('aria-expanded', 'false');
        };
        document.addEventListener('click', (event) => {
            if (modePicker && modePicker.contains(event.target)) return;
            modeMenu.classList.add('hidden');
            modeButton.setAttribute('aria-expanded', 'false');
        });
    }
    uploadBtn.onclick = () => fileInput.click();
    // ── PDF / Document permission & auto-fetch ────────────────────────────────

    const PAGE_DOC_EXTENSIONS = /\.(pdf|docx|doc|txt|md|xlsx|csv)([?#].*)?$/i;
    const _promptedDocUrls = new Set(); // avoid re-prompting on same page

    const detectPageDocumentLinks = () => {
        const links = [];
        document.querySelectorAll('a[href]').forEach((a) => {
            const href = (a.getAttribute('href') || '').trim();
            if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
            const abs = new URL(href, window.location.href).href;
            if (PAGE_DOC_EXTENSIONS.test(abs) && !_promptedDocUrls.has(abs)) {
                const label = (a.textContent || '').trim().replace(/\s+/g, ' ') || abs.split('/').pop();
                const ext = (abs.match(PAGE_DOC_EXTENSIONS) || [])[1]?.toLowerCase() || 'file';
                links.push({ url: abs, label, ext });
                _promptedDocUrls.add(abs);
            }
        });
        // Deduplicate by URL
        return [...new Map(links.map(l => [l.url, l])).values()].slice(0, 6);
    };

    const fetchAndIndexUrlDocument = async (doc) => {
        const statusEl = addMessage(
            `<span class="flow-diagram-generating">⚙️ Reading <strong>${escapeHtml(doc.label)}</strong>…</span>`,
            'bot', { persist: false, raw: true }
        );
        try {
            const result = await sendBackendMessage('fetchUrlDocument', {
                url: doc.url,
                page_url: window.location.href,
            });
            if (result.error || !result.ok) {
                statusEl.innerHTML = formatBotMessage(`Could not read **${doc.label}**: ${result.error || 'unknown error'}`);
                return;
            }
            // Treat it like a manual document upload
            uploadedDocument = {
                document_id: result.document_id,
                filename: result.filename,
                source_url: result.source_url,
                extracted_text: result.extracted_text || '',
                text_chars: result.chars,
            };
            setDocumentMode('document');
            updateDocumentChip();
            statusEl.innerHTML = formatBotMessage(
                `✅ **${result.filename}** loaded (${Math.round(result.chars / 1000)}k chars, ${result.chunks} chunks). Ask me anything about it!`
            );
            setFollowUps(['Summarize this document', 'List key points', 'Find risks or gaps']);
        } catch (err) {
            statusEl.innerHTML = formatBotMessage(`Failed to read **${doc.label}**: ${err.message}`);
        }
    };

    const detectAndPromptPageDocuments = () => {
        const docs = detectPageDocumentLinks();
        if (!docs.length) return;

        const typeLabel = (ext) => {
            if (ext === 'pdf') return 'PDF';
            if (['doc', 'docx'].includes(ext)) return 'Word doc';
            if (ext === 'xlsx') return 'Spreadsheet';
            return ext.toUpperCase();
        };

        const docListHtml = docs.map((doc, i) =>
            `<div class="page-doc-item" data-doc-index="${i}">
                <span class="page-doc-icon">${doc.ext === 'pdf' ? '📝' : '📄'}</span>
                <span class="page-doc-name" title="${escapeHtml(doc.url)}">${escapeHtml(doc.label)}</span>
                <span class="page-doc-badge">${typeLabel(doc.ext)}</span>
            </div>`
        ).join('');

        const card = addMessage(
            `<div class="page-doc-permission-card">
                <div class="page-doc-permission-header">
                    <span class="page-doc-permission-icon">📎</span>
                    <span class="page-doc-permission-title">Documents found on this page</span>
                </div>
                <p class="page-doc-permission-desc">I found ${docs.length} document${docs.length > 1 ? 's' : ''} linked on this page. Should I read ${docs.length > 1 ? 'them' : 'it'} so you can ask questions about the content?</p>
                <div class="page-doc-list">${docListHtml}</div>
                <div class="page-doc-permission-actions">
                    <button class="page-doc-btn-all" data-action="read-all">Read all</button>
                    ${docs.length > 1 ? '<button class="page-doc-btn-pick" data-action="pick">Choose one</button>' : ''}
                    <button class="page-doc-btn-skip" data-action="skip">Skip</button>
                </div>
            </div>`,
            'bot', { persist: false, raw: true }
        );

        // Store docs list on card for click handler
        card._pageDocsList = docs;

        card.querySelector('[data-action="read-all"]').onclick = async () => {
            card.querySelector('.page-doc-permission-actions').innerHTML = '<span style="font-size:12px;color:var(--cb-text-muted);">Reading…</span>';
            for (const doc of docs) {
                await fetchAndIndexUrlDocument(doc);
            }
            card.remove();
        };

        const pickBtn = card.querySelector('[data-action="pick"]');
        if (pickBtn) {
            pickBtn.onclick = () => {
                // Toggle individual pick buttons on each doc item
                card.querySelectorAll('.page-doc-item').forEach((item, i) => {
                    item.style.cursor = 'pointer';
                    item.title = 'Click to read this document';
                    item.onclick = async () => {
                        item.onclick = null;
                        await fetchAndIndexUrlDocument(docs[i]);
                        card.remove();
                    };
                });
                pickBtn.textContent = 'Click a document above';
                pickBtn.disabled = true;
            };
        }

        card.querySelector('[data-action="skip"]').onclick = () => card.remove();
    };

    // ── end PDF permission ────────────────────────────────

    documentChip.onclick = (event) => {
        const modeButton = event.target.closest('[data-document-mode]');
        if (modeButton) {
            const mode = modeButton.dataset.documentMode || 'website';
            setDocumentMode(mode);
            updateDocumentChip();
            const modeMessage = {
                website: 'Website chat is active.',
                document: 'Document chat is active.',
                compare: ''
            };
            if (modeMessage[mode]) {
                addMessage(modeMessage[mode], 'bot', { persist: false });
            }
            return;
        }
        if (!event.target.closest('[data-remove-document]')) return;
        uploadedDocument = null;
        fetchedWebpageText = '';
        fetchedWebpageUrl = '';
        compareSourceBDocument = null;
        updateDocumentChip();
        updateCompareToolPanel();
        setDocumentMode('website');
        addMessage('Document removed. I will answer from the website again.', 'bot', { persist: false });
    };

    // Fetch webpage text for compare mode
    const fetchWebpageForCompare = async () => {
        const url = (webpageUrlInput.value || '').trim();
        if (!url) {
            webpageUrlInput.focus();
            return;
        }
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            addMessage('Please enter a full URL starting with https:// or http://', 'bot', { persist: false });
            return;
        }

        webpageFetchBtn.disabled = true;
        webpageFetchBtn.textContent = 'Fetching…';
        const status = addMessage(`Fetching content from ${shortDisplayUrl(url)}…`, 'bot', { persist: false });
        status.classList.add('typing');

        try {
            const result = await sendBackendMessage('fetchWebpageContent', { url });
            fetchedWebpageText = result.text || '';
            fetchedWebpageUrl = url;

            // Show a chip confirming the fetch
            const existing = webpagePanel.querySelector('.webpage-chip');
            if (existing) existing.remove();

            const chip = document.createElement('div');
            chip.className = 'webpage-chip';
            chip.innerHTML = `
                <span class="webpage-chip-icon">
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                </span>
                <span class="webpage-chip-url" title="${escapeHtml(url)}">${escapeHtml(shortDisplayUrl(url))}</span>
                <span style="font-size:11px;color:var(--cb-text-muted);">${Math.round((result.chars || fetchedWebpageText.length) / 1000)}k chars</span>
                <button class="webpage-chip-remove" data-remove-webpage title="Remove">Remove</button>
            `;
            chip.querySelector('[data-remove-webpage]').onclick = () => {
                fetchedWebpageText = '';
                fetchedWebpageUrl = '';
                chip.remove();
                addMessage('Webpage removed. Now I will compare your document with the current website page.', 'bot', { persist: false });
                updateCompareToolPanel();
            };
            webpagePanel.appendChild(chip);

            status.remove();
            addMessage(`Got it — **${shortDisplayUrl(url)}** loaded (${Math.round(fetchedWebpageText.length / 1000)}k chars). Now ask me to compare it with your document.`, 'bot', { persist: false });
            setFollowUps(pageSpecificSuggestions([], 3));
            updateCompareToolPanel();
        } catch (error) {
            status.remove();
            addMessage('Fetch failed: ' + error.message, 'bot', { persist: false });
        } finally {
            webpageFetchBtn.disabled = false;
            webpageFetchBtn.textContent = 'Fetch';
        }
    };

    webpageFetchBtn.onclick = fetchWebpageForCompare;
    webpageUrlInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            fetchWebpageForCompare();
        }
    };
    if (compareToggleBtn) {
        compareToggleBtn.onclick = () => {
            compareAdvancedOpen = !compareAdvancedOpen;
            updateCompareToolPanel();
        };
    }
    if (compareAUploadBtn) {
        compareAUploadBtn.onclick = () => {
            compareAdvancedOpen = true;
            compareSourceA = 'document';
            updateCompareToolPanel();
            fileInput.click();
        };
    }
    if (compareACurrentBtn) {
        compareACurrentBtn.onclick = async () => {
            compareSourceA = 'current';
            await prepareLivePageContent(null);
            updateCompareToolPanel();
        };
    }
    if (compareBFetchBtn) {
        compareBFetchBtn.onclick = () => {
            compareAdvancedOpen = true;
            compareSourceB = 'fetched';
            updateCompareToolPanel();
            webpageUrlInput.focus();
        };
    }
    if (compareBUploadBtn) {
        compareBUploadBtn.onclick = () => {
            compareAdvancedOpen = true;
            compareSourceB = 'uploaded';
            updateCompareToolPanel();
            compareBFileInput?.click();
        };
    }
    if (compareBCurrentBtn) {
        compareBCurrentBtn.onclick = async () => {
            compareSourceB = 'current';
            await prepareLivePageContent(null);
            updateCompareToolPanel();
        };
    }
    if (compareBFileInput) {
        compareBFileInput.onchange = () => uploadCompareSourceBDocument(compareBFileInput.files && compareBFileInput.files[0]);
    }
    if (compareRunBtn) {
        compareRunBtn.onclick = runCompareToolFromPanel;
    }
    if (compareGoalSelect) {
        compareGoalSelect.onchange = updateCompareToolPanel;
    }
    fileInput.onchange = () => uploadDocument(fileInput.files && fileInput.files[0]);
    reindexBtn.onclick = async () => {
        const status = addMessage('Refreshing page index...', 'bot', { persist: false });
        status.classList.add('typing');
        try {
            activeScopeUrl = window.location.href;
            indexedContentHash = '';
            pageContentHash = '';
            setScope('page');
            await ensureIndexed(true, status);
            status.remove();
            addMessage('Page index refreshed.', 'bot');
        } catch (error) {
            status.remove();
            addMessage('Refresh failed: ' + error.message, 'bot');
        }
    };
    crawlBtn.onclick = async () => {
        const status = addMessage('Crawling website...', 'bot', { persist: false });
        status.classList.add('typing');
        try {
            await crawlWebsite(status);
            status.remove();
            addMessage('Website crawl complete. You can now ask questions across all indexed pages.', 'bot');
        } catch (error) {
            status.remove();
            addMessage('Website crawl failed: ' + error.message, 'bot');
        }
    };
    settingsBtn.onclick = () => {
        settingsPanel.classList.toggle('hidden');
    };
    clearBtn.onclick = () => {
        localStorage.removeItem(chatStorageKey);
        conversationHistory = [];
        conversationMemory = {};
        sessionStorage.removeItem(historyKey);
        sessionStorage.removeItem(memoryKey);
        messagesContainer.innerHTML = '';
        addMessage('Chat history cleared. How can I help you today?', 'bot', { persist: false });
        settingsPanel.classList.add('hidden');
    };
    crawlLimitInput.onchange = saveSettings;
    autoIndexInput.onchange = () => {
        saveSettings();
        if (autoIndexInput.checked) {
            startBackgroundPageIndexing(300);
        }
    };
    conciseInput.onchange = saveSettings;
    settingsTabs.forEach((tab) => {
        tab.onclick = () => {
            const target = tab.id.replace('settings-tab-', '');
            settingsTabs.forEach((item) => item.classList.toggle('active', item === tab));
            settingsContents.forEach((content) => {
                content.classList.toggle('hidden', content.id !== `settings-content-${target}`);
            });
        };
    });
    Object.values(profileFields).forEach((element) => {
        if (element) element.oninput = saveUserProfile;
    });
    if (profileCustomFieldsInput) profileCustomFieldsInput.oninput = saveUserProfile;
    loadSettings();
    loadUserProfile();
    loadModelOptions();
    loadChatHistory();
    showAutofillSessionReminder();
    setScope(scopeSelect.value || 'page');
    checkBackendHealth();
    startPlaceholderRotation();
    startBackgroundPageIndexing();
})();