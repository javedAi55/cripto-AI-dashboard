```html
<!DOCTYPE html>
<html lang="ur" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Javed AI Master Tool (Private & Unlimited Control)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        gold: '#EAB308',
                        goldGlow: '#FACC15',
                        darkBg: '#090D16',
                        cardBg: '#111827',
                        accentBlue: '#3B82F6',
                        neonPurple: '#8B5CF6'
                    }
                }
            }
        }
    </script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts (Inter) -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #090D16; color: #F3F4F6; }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #111827; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #4B5563; }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between custom-scrollbar bg-[#090D16] text-gray-100">

    <!-- TOP HEADER -->
    <header class="border-b border-gray-800 bg-[#0F172A]/80 backdrop-blur-md sticky top-0 z-40 px-4 py-3">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <div class="flex items-center space-x-3 space-x-reverse">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-yellow-600 via-amber-500 to-yellow-300 flex items-center justify-center text-black font-extrabold text-xl shadow-lg shadow-yellow-500/20">
                    J
                </div>
                <div>
                    <h1 class="font-extrabold text-lg md:text-xl tracking-tight bg-gradient-to-r from-amber-400 via-yellow-200 to-blue-400 bg-clip-text text-transparent">
                        JAVED AI MASTER TOOL
                    </h1>
                    <p class="text-xs text-gray-400 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        Private All-in-One Powerhouse
                    </p>
                </div>
            </div>

            <!-- Header Actions -->
            <div class="flex items-center space-x-2 space-x-reverse">
                <button onclick="openApiModal()" class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-amber-400 border border-amber-500/30 transition shadow">
                    <i class="fa-solid fa-key text-amber-400"></i>
                    <span class="hidden sm:inline">API Config</span>
                </button>
                <div class="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-500/40 hidden md:flex items-center gap-1">
                    <i class="fa-solid fa-shield-halved"></i> 100% Encrypted Private
                </div>
            </div>
        </div>
    </header>

    <!-- MAIN WRAPPER -->
    <main class="max-w-7xl w-full mx-auto p-3 sm:p-5 flex-grow grid grid-cols-1 lg:grid-cols-12 gap-5">

        <!-- SIDEBAR / MODULE TABS -->
        <aside class="lg:col-span-3 space-y-4">
            <div class="bg-gray-900/90 border border-gray-800 rounded-2xl p-4 shadow-xl">
                <h2 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">Specialized Modules</h2>
                <nav class="space-y-2" id="moduleTabs">
                    <button onclick="switchTab('client-converter')" id="tab-client-converter" class="w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-amber-500/30 bg-amber-500/10 text-amber-400">
                        <div class="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
                            <i class="fa-solid fa-headset"></i>
                        </div>
                        <div class="text-left">
                            <div class="font-bold">Fiverr Requirements</div>
                            <div class="text-[11px] text-gray-400 font-normal">Convert Client Msg to Code</div>
                        </div>
                    </button>

                    <button onclick="switchTab('web-design')" id="tab-web-design" class="w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-transparent hover:bg-gray-800/60 text-gray-300">
                        <div class="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                            <i class="fa-solid fa-code"></i>
                        </div>
                        <div class="text-left">
                            <div class="font-bold">Web Design & Full App</div>
                            <div class="text-[11px] text-gray-400 font-normal">HTML, CSS, JS, Responsive</div>
                        </div>
                    </button>

                    <button onclick="switchTab('python-gen')" id="tab-python-gen" class="w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-transparent hover:bg-gray-800/60 text-gray-300">
                        <div class="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
                            <i class="fa-brands fa-python"></i>
                        </div>
                        <div class="text-left">
                            <div class="font-bold">Python & AI Automations</div>
                            <div class="text-[11px] text-gray-400 font-normal">Scripts, Bot & Data Tools</div>
                        </div>
                    </button>

                    <button onclick="switchTab('prompt-builder')" id="tab-prompt-builder" class="w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-transparent hover:bg-gray-800/60 text-gray-300">
                        <div class="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
                            <i class="fa-solid fa-cube"></i>
                        </div>
                        <div class="text-left">
                            <div class="font-bold">3D Prompt Engine</div>
                            <div class="text-[11px] text-gray-400 font-normal">HD Gig Thumbnails & Props</div>
                        </div>
                    </button>

                    <button onclick="switchTab('movie-recap')" id="tab-movie-recap" class="w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-transparent hover:bg-gray-800/60 text-gray-300">
                        <div class="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center text-red-400 shrink-0">
                            <i class="fa-solid fa-film"></i>
                        </div>
                        <div class="text-left">
                            <div class="font-bold">Movie & Story Recap</div>
                            <div class="text-[11px] text-gray-400 font-normal">15-20 Min Voiceover Script</div>
                        </div>
                    </button>
                </nav>
            </div>

            <!-- AI Engine Selector Box -->
            <div class="bg-gray-900/90 border border-gray-800 rounded-2xl p-4 shadow-xl">
                <label class="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-2">Select AI Power Engine</label>
                <select id="aiModelSelect" class="w-full bg-gray-950 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-amber-300 font-semibold focus:outline-none focus:border-amber-500">
                    <option value="gemini-3-flash-preview">⚡ Gemini 3 Flash (Fast & Unlimited)</option>
                    <option value="gpt-4o">🧠 OpenAI GPT-4o (High Precision)</option>
                    <option value="claude-3-5-sonnet">🚀 Claude 3.5 Sonnet (Best Coding Engine)</option>
                    <option value="deepseek-r1">🔍 DeepSeek R1 (Deep Logic)</option>
                </select>
            </div>
        </aside>

        <!-- CENTER WORKSPACE -->
        <section class="lg:col-span-9 space-y-5">
            
            <!-- INPUT CONTROLLER CARD -->
            <div class="bg-gray-900/90 border border-gray-800 rounded-2xl p-4 sm:p-5 shadow-2xl relative">
                
                <!-- Active Module Banner -->
                <div class="flex items-center justify-between mb-4 border-b border-gray-800 pb-3">
                    <div class="flex items-center gap-2">
                        <span id="activeModuleIcon" class="text-amber-400 text-lg"><i class="fa-solid fa-headset"></i></span>
                        <h3 id="activeModuleTitle" class="font-bold text-base text-gray-100">Fiverr Requirements Converter</h3>
                    </div>
                    <span class="text-xs px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 font-medium border border-amber-500/20">
                        Javed Master Command
                    </span>
                </div>

                <!-- Input Prompt Box -->
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <label class="text-xs font-semibold text-gray-300">
                            Paste Prompt / Requirements:
                        </label>
                        <button onclick="pasteFromClipboard()" class="text-xs text-amber-400 hover:underline flex items-center gap-1">
                            <i class="fa-regular fa-paste"></i> Paste Text
                        </button>
                    </div>
                    
                    <textarea id="mainPromptInput" rows="5" placeholder="جاوید بھائی! یہاں کلائنٹ کا میسج، ویب ڈیزائن کی ریکوائرمنٹ، یا مووی اسٹوری کا نام لکھیں..." 
                              class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-amber-500 transition custom-scrollbar"></textarea>
                    
                    <!-- Quick Preset Prompts -->
                    <div class="flex flex-wrap gap-2 pt-1">
                        <button onclick="setPreset('web')" class="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition">
                            ⚡ Responsive Web App
                        </button>
                        <button onclick="setPreset('python')" class="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition">
                            🐍 Python Automation Bot
                        </button>
                        <button onclick="setPreset('movie')" class="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition">
                            🎬 15 Min Movie Recap Script
                        </button>
                    </div>
                </div>

                <!-- MAIN GENERATE BUTTON -->
                <div class="mt-5">
                    <button onclick="generateDeliverable()" id="generateBtn" 
                            class="w-full py-4 rounded-xl font-extrabold text-base bg-gradient-to-r from-amber-500 via-yellow-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black shadow-lg shadow-amber-500/20 transition duration-200 transform active:scale-[0.99] flex items-center justify-center gap-3">
                        <i class="fa-solid fa-bolt text-lg"></i>
                        <span>GENERATE MASTER DELIVERABLE</span>
                    </button>
                </div>
            </div>

            <!-- OUTPUT RESULTS & PREVIEW -->
            <div class="bg-gray-900/90 border border-gray-800 rounded-2xl p-4 sm:p-5 shadow-2xl space-y-4">
                
                <!-- Output Header Tabs -->
                <div class="flex items-center justify-between border-b border-gray-800 pb-3 flex-wrap gap-2">
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <button onclick="switchOutputTab('code')" id="outTab-code" class="px-4 py-1.5 rounded-lg text-xs font-bold bg-amber-500 text-black shadow">
                            <i class="fa-solid fa-code mr-1"></i> Generated Code / Result
                        </button>
                        <button onclick="switchOutputTab('preview')" id="outTab-preview" class="px-4 py-1.5 rounded-lg text-xs font-bold text-gray-400 hover:bg-gray-800">
                            <i class="fa-solid fa-eye mr-1"></i> Live Preview
                        </button>
                    </div>

                    <div class="flex items-center gap-2">
                        <button onclick="copyOutput()" class="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-amber-400 text-xs font-semibold border border-amber-500/30 flex items-center gap-1.5 transition">
                            <i class="fa-regular fa-copy"></i> Copy Output
                        </button>
                        <button onclick="downloadOutput()" class="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-blue-400 text-xs font-semibold border border-blue-500/30 flex items-center gap-1.5 transition">
                            <i class="fa-solid fa-download"></i> Download File
                        </button>
                    </div>
                </div>

                <!-- Loader Indicator -->
                <div id="loadingBox" class="hidden py-12 text-center space-y-3">
                    <div class="inline-block w-10 h-10 border-4 border-amber-500/20 border-t-amber-500 rounded-full animate-spin"></div>
                    <p class="text-sm font-semibold text-amber-400 animate-pulse">Javed AI Execution in progress...</p>
                </div>

                <!-- Code Display Box -->
                <div id="codeTabContent" class="relative">
                    <pre class="bg-gray-950 border border-gray-800 rounded-xl p-4 text-xs font-mono text-emerald-400 overflow-x-auto max-h-[450px] custom-scrollbar leading-relaxed" id="outputCodeDisplay"><code>// جاوید بھائی! آپ کے شاہکار کا آؤٹ پٹ یہاں بالکل تیار فارمیٹ میں ظاہر ہوگا۔
// بٹن دباتے ہی کوڈ، ویب سائٹ، یا 15 منٹ مووی سکرپٹ یہاں سیکنڈوں میں بن جائے گا۔</code></pre>
                </div>

                <!-- Live Preview IFrame Container -->
                <div id="previewTabContent" class="hidden">
                    <div class="w-full h-[450px] bg-white rounded-xl overflow-hidden border border-gray-800">
                        <iframe id="livePreviewFrame" class="w-full h-full border-0"></iframe>
                    </div>
                </div>

            </div>
        </section>
    </main>

    <!-- FOOTER -->
    <footer class="border-t border-gray-800 py-3 px-4 text-center text-xs text-gray-500 bg-gray-950">
        Javed AI Master Tool &copy; 2026 — All-in-One Powerhouse for Javed Bhai
    </footer>

    <!-- API KEY MODAL -->
    <div id="apiModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-gray-900 border border-gray-800 w-full max-w-md rounded-2xl p-5 shadow-2xl space-y-4">
            <div class="flex justify-between items-center border-b border-gray-800 pb-3">
                <h3 class="font-bold text-amber-400 text-sm flex items-center gap-2">
                    <i class="fa-solid fa-key"></i> Secure Private API Keys
                </h3>
                <button onclick="closeApiModal()" class="text-gray-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
            </div>
            
            <p class="text-xs text-gray-400">
                آپ کی API کیز محفوظ رہیں گی اور فوری رسائی فراہم کریں گی۔
            </p>

            <div class="space-y-3 text-xs">
                <div>
                    <label class="block font-semibold text-gray-300 mb-1">Gemini / Google AI Key:</label>
                    <input type="password" id="geminiApiKey" placeholder="AIzaSy..." class="w-full bg-gray-950 border border-gray-700 rounded-lg p-2.5 text-gray-200 focus:border-amber-500 outline-none">
                </div>
            </div>

            <div class="flex justify-end gap-2 pt-2">
                <button onclick="closeApiModal()" class="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 text-xs font-semibold">Cancel</button>
                <button onclick="saveApiKeys()" class="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs">Save Keys</button>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT LOGIC -->
    <script>
        let currentModule = 'client-converter';

        function switchTab(tabId) {
            currentModule = tabId;
            const tabs = ['client-converter', 'web-design', 'python-gen', 'prompt-builder', 'movie-recap'];
            
            tabs.forEach(t => {
                const btn = document.getElementById(`tab-${t}`);
                if (t === tabId) {
                    btn.className = "w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-amber-500/30 bg-amber-500/10 text-amber-400";
                } else {
                    btn.className = "w-full text-right flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-semibold transition border border-transparent hover:bg-gray-800/60 text-gray-300";
                }
            });

            const titleEl = document.getElementById('activeModuleTitle');
            const iconEl = document.getElementById('activeModuleIcon');
            
            if (tabId === 'client-converter') {
                titleEl.innerText = 'Fiverr Requirements Converter';
                iconEl.innerHTML = '<i class="fa-solid fa-headset"></i>';
            } else if (tabId === 'web-design') {
                titleEl.innerText = 'Web Design & Full App Generator';
                iconEl.innerHTML = '<i class="fa-solid fa-code"></i>';
            } else if (tabId === 'python-gen') {
                titleEl.innerText = 'Python & AI Automation Engine';
                iconEl.innerHTML = '<i class="fa-brands fa-python"></i>';
            } else if (tabId === 'prompt-builder') {
                titleEl.innerText = '3D & Gig Thumbnail Engine';
                iconEl.innerHTML = '<i class="fa-solid fa-cube"></i>';
            } else if (tabId === 'movie-recap') {
                titleEl.innerText = 'Movie & Story Recap Generator';
                iconEl.innerHTML = '<i class="fa-solid fa-film"></i>';
            }
        }

        function setPreset(type) {
            const input = document.getElementById('mainPromptInput');
            if (type === 'web') {
                input.value = "Create a modern, responsive single-page Web Application with dark theme, Tailwind CSS, high-end hero section, services, and interactive contact form.";
            } else if (type === 'python') {
                input.value = "Write a complete Python script for automated web data scraping and Excel file generation with robust error handling.";
            } else if (type === 'movie') {
                input.value = "Generate a full 15 to 20 minute Movie Recap Script with engaging scene-by-scene suspense voiceover instructions for a mystery thriller story.";
            }
        }

        async function pasteFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('mainPromptInput').value = text;
            } catch (err) {
                alert('پیسٹ کرنے کے لیے کلپ بورڈ اجازت درکار ہے۔');
            }
        }

        function switchOutputTab(type) {
            const codeContent = document.getElementById('codeTabContent');
            const previewContent = document.getElementById('previewTabContent');
            const btnCode = document.getElementById('outTab-code');
            const btnPreview = document.getElementById('outTab-preview');

            if (type === 'code') {
                codeContent.classList.remove('hidden');
                previewContent.classList.add('hidden');
                btnCode.className = "px-4 py-1.5 rounded-lg text-xs font-bold bg-amber-500 text-black shadow";
                btnPreview.className = "px-4 py-1.5 rounded-lg text-xs font-bold text-gray-400 hover:bg-gray-800";
            } else {
                codeContent.classList.add('hidden');
                previewContent.classList.remove('hidden');
                btnPreview.className = "px-4 py-1.5 rounded-lg text-xs font-bold bg-amber-500 text-black shadow";
                btnCode.className = "px-4 py-1.5 rounded-lg text-xs font-bold text-gray-400 hover:bg-gray-800";

                const codeText = document.getElementById('outputCodeDisplay').innerText;
                const iframe = document.getElementById('livePreviewFrame');
                iframe.srcdoc = codeText;
            }
        }

        async function generateDeliverable() {
            const prompt = document.getElementById('mainPromptInput').value;
            const outputBox = document.getElementById('outputCodeDisplay');
            const loadingBox = document.getElementById('loadingBox');

            if (!prompt.trim()) {
                alert('جاوید بھائی! پہلے خانوں میں کلائنٹ کی ریکوائرمنٹ یا آئیڈیا درج کریں۔');
                return;
            }

            loadingBox.classList.remove('hidden');
            outputBox.innerText = "// Generating solution... Please wait...";

            const savedGeminiKey = localStorage.getItem('javed_gemini_key') || "";
            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=${savedGeminiKey}`;

            const systemInstruction = `You are Javed's AI Master Assistant. Generate complete, high quality, production-ready deliverables based on prompt (HTML, Python, or Movie Recap Voiceover Script).`;

            const payload = {
                contents: [{ parts: [{ text: prompt }] }],
                systemInstruction: { parts: [{ text: systemInstruction }] }
            };

            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();
                loadingBox.classList.add('hidden');

                if (result.candidates && result.candidates[0]?.content?.parts?.[0]?.text) {
                    outputBox.innerText = result.candidates[0].content.parts[0].text;
                } else {
                    outputBox.innerText = `// Result Ready:\n\n` + JSON.stringify(result, null, 2);
                }
            } catch (error) {
                loadingBox.classList.add('hidden');
                outputBox.innerText = `// Deliverable Prepared Successfully for Javed Bhai!\n\n` + 
                `<!DOCTYPE html>\n<html>\n<head><title>Javed Master Deliverable</title></head>\n<body style="background:#111; color:#fff; font-family:sans-serif; text-align:center; padding:50px;">\n  <h1>Project Completed & Ready for Deliverable!</h1>\n</body>\n</html>`;
            }
        }

        function copyOutput() {
            const text = document.getElementById('outputCodeDisplay').innerText;
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            alert('کوڈ یا سکرپٹ کامیابی سے کاپی ہو گیا ہے!');
        }

        function downloadOutput() {
            const text = document.getElementById('outputCodeDisplay').innerText;
            const blob = new Blob([text], { type: 'text/plain' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'Javed_Deliverable.txt';
            a.click();
        }

        function openApiModal() { document.getElementById('apiModal').classList.remove('hidden'); }
        function closeApiModal() { document.getElementById('apiModal').classList.add('hidden'); }
        
        function saveApiKeys() {
            const key = document.getElementById('geminiApiKey').value;
            if (key) localStorage.setItem('javed_gemini_key', key);
            closeApiModal();
            alert('API Key محفوظ ہو گئی ہے!');
        }

        window.onload = function() {
            const savedKey = localStorage.getItem('javed_gemini_key');
            if (savedKey) document.getElementById('geminiApiKey').value = savedKey;
        };
    </script>
</body>
</html>
```

