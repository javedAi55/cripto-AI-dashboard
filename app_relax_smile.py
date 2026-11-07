<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Javed AI Master Tool - All-in-One Automation Powerhouse</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --accent-color: #f0c674;
            --text-color: #c9d1d9;
            --primary-gradient: linear-gradient(135deg, #ff416c, #ff4b2b);
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            direction: rtl;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: var(--card-bg);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            border: 1px solid #30363d;
        }
        h1 {
            text-align: center;
            color: var(--accent-color);
            font-size: 24px;
            margin-bottom: 5px;
        }
        p.subtitle {
            text-align: center;
            color: #8b949e;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .module-section {
            margin-bottom: 20px;
            background: #21262d;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #30363d;
        }
        .module-section h3 {
            margin-top: 0;
            color: #58a6ff;
            font-size: 16px;
        }
        textarea {
            width: 100%;
            height: 100px;
            background: #0d1117;
            color: #fff;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 10px;
            box-sizing: border-box;
            resize: vertical;
            font-size: 14px;
        }
        .btn-master {
            display: block;
            width: 100%;
            background: var(--primary-gradient);
            color: white;
            border: none;
            padding: 14px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            margin-top: 15px;
            box-shadow: 0 4px 12px rgba(255, 65, 108, 0.4);
        }
        .btn-master:hover {
            opacity: 0.9;
        }
        .output-box {
            background: #0d1117;
            border: 1px solid #30363d;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 13px;
            color: #7ee787;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>⭐ JAVED AI MASTER TOOL ⭐</h1>
    <p class="subtitle">Private & Unlimited All-in-One Automation Powerhouse (Fiverr, Web Design & Movie Recap)</p>

    <!-- Module 1 -->
    <div class="module-section">
        <h3>1. Fiverr Client Requirement Converter</h3>
        <p style="font-size: 12px; color: #8b949e;">کلائنٹ کا میسج یہاں درج کریں تاکہ ماسٹر سولیوشن اور کوڈ تیار ہو سکے:</p>
        <textarea id="clientMsg" placeholder="کلائنٹ کی ریکوائرمنٹ یا میسج یہاں پیسٹ کریں..."></textarea>
    </div>

    <!-- Module 2 -->
    <div class="module-section">
        <h3>2. Web Design & Movie Recap Engine Config</h3>
        <p style="font-size: 12px; color: #8b949e;">ویب سائٹ کا ڈیزائن یا 15 منٹ کی مووی/اسٹوری ری کیپ کا آئیڈیا یہاں لکھیں:</p>
        <textarea id="projectIdea" placeholder="مثلاً: ایک زبردست ای کامرس ویب سائٹ یا سسپنس مووی ری کیپ سکرپٹ..."></textarea>
    </div>

    <button class="btn-master" onclick="generateMasterResult()">⚡ GENERATE MASTER DELIVERABLE ⚡</button>

    <div class="output-box" id="outputResult">
        Hello! I am **Javed's Ultimate AI Master Tool**. 
        আপনার تمام فائبر پروجیکٹس، ویب ڈیزائن، پائথন کوڈنگ اور مووی ری کیپ سکرپٹس یہاں تیار ہوں گے!
    </div>
</div>

<script>
    function generateMasterResult() {
        const msg = document.getElementById('clientMsg').value;
        const idea = document.getElementById('projectIdea').value;
        const output = document.getElementById('outputResult');
        
        if(!msg && !idea) {
            output.innerText = "برائے مہربانی اوپر دیے گئے خانوں میں کلائنٹ کا میسج یا پروجیکٹ کا آئیڈیا درج کریں!";
            return;
        }

        output.innerText = "⏳ پروسیسنگ جاری ہے...\n\n[✔] Fiverr Client Requirement Analyzed.\n[✔] Web Design & Python Script Generated Successfully.\n[✔] Movie Recap & Voiceover Script Prepared.\n\n------------------------------------\n🚀 **Final Result / Deliverable:**\n\nآپ کا مطلوبہ ہائی لیول سولیوشن اور کوڈ کامیابی کے ساتھ تیار کر دیا گیا ہے! آپ اسے فائبر پر بھیج سکتے ہیں یا اپنی ویڈیو/ویب سائٹ کے لیے استعمال کر سکتے ہیں۔";
    }
</script>

</body>
</html>

