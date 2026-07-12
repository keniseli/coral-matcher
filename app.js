const API_BASE = "http://localhost:8080";
let currentFilePayload = null;
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const uploadPrompt = document.getElementById('uploadPrompt');
const uploadDropZone = document.getElementById('uploadDropZone');
const clearImageBtn = document.getElementById('clearImageBtn');
const snackbar = document.getElementById('snackbar');

// Lightweight Native In-App Notification Snackbar Engine
function showNotification(message, type = 'success') {
    
    // Theme color dictionary mapping
    const styles = {
        success: ['border-emerald-500/30', 'text-emerald-400', 'bg-emerald-950/80', 'backdrop-blur-md'],
        error: ['border-red-500/30', 'text-red-400', 'bg-red-950/80', 'backdrop-blur-md'],
        info: ['border-blue-500/30', 'text-blue-400', 'bg-blue-950/80', 'backdrop-blur-md']
    };

    // Reset styles cleanly
    snackbar.className = "fixed bottom-6 right-6 z-50 pointer-events-none p-4 rounded-xl border font-mono text-sm font-semibold shadow-2xl transition-all duration-300 opacity-0 translate-y-4";
    
    // Inject correct theme modifiers
    snackbar.classList.add(...styles[type]);
    snackbar.innerText = message;

    // Trigger slide-up and fade-in animations
    setTimeout(() => {
        snackbar.classList.remove('opacity-0', 'translate-y-4');
        snackbar.classList.add('opacity-100', 'translate-y-0');
    }, 50);

    // Fade-out decay sequence after 4 seconds
    setTimeout(() => {
        snackbar.classList.remove('opacity-100', 'translate-y-0');
        snackbar.classList.add('opacity-0', 'translate-y-4');
    }, 4000);
}


function resetDashboardState() {
    document.getElementById('statusPlaceholder').classList.remove('hidden');
    document.getElementById('matchDisplayArea').classList.add('hidden');
    document.getElementById('newCoralActionPanel').classList.add('hidden');
    document.getElementById('cardsList').innerHTML = '';
    imagePreview.src = '';
    imagePreview.classList.add('hidden');
    uploadPrompt.classList.remove('hidden');
    clearImageBtn.classList.add('hidden');
    uploadDropZone.className = "group border-2 border-dashed border-slate-700 hover:border-emerald-500/70 transition-all rounded-2xl bg-slate-950 cursor-pointer w-full aspect-[4/3] flex flex-col justify-center items-center shadow-inner relative overflow-hidden";
    imageInput.value = "";
    currentFilePayload = null;
}

clearImageBtn.onclick = function (e) {
    e.stopPropagation(); // Prevents launching OS file chooser modal loop window
    resetDashboardState();
};

document.getElementById('imageInput').onchange = function (e) {
    const file = e.target.files[0];
    const site = document.getElementById('siteName').value.trim();

    if (!file) return;
    if (!site) {
        showNotification("Please select a target dive site location first.", "error");
        resetDashboardState();
        return;
    }

    currentFilePayload = file;

    // Trigger preview container and visibility classes
    imagePreview.src = URL.createObjectURL(file);
    imagePreview.classList.remove('hidden');
    uploadPrompt.classList.add('hidden');
    clearImageBtn.classList.remove('hidden');
    uploadDropZone.className = "group border border-slate-800 transition-all rounded-2xl bg-slate-950 cursor-pointer w-full aspect-[4/3] flex flex-col justify-center items-center shadow-2xl relative overflow-hidden";
    
    document.getElementById('statusPlaceholder').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('matchDisplayArea').classList.add('hidden');
    document.getElementById('newCoralActionPanel').classList.add('hidden');

    let formData = new FormData();
    formData.append('image', file);
    formData.append('site_name', site);

    fetch(`${API_BASE}/match-coral`, { method: 'POST', body: formData })
        .then(res => {
            if (!res.ok) throw new Error("API route lookup error context.");
            return res.json();
        })
        .then(data => {
            document.getElementById('loader').classList.add('hidden');
            document.getElementById('matchDisplayArea').classList.remove('hidden');
            document.getElementById('newCoralActionPanel').classList.remove('hidden');

            const listContainer = document.getElementById('cardsList');
            listContainer.innerHTML = '';

            if (!data.matches || data.matches.length === 0) {
                listContainer.innerHTML = `
                    <div class="p-6 bg-slate-950 text-slate-500 rounded-xl border border-slate-800 font-mono text-xs text-center">
                        Zero vector alignments matched within site parameters. Click the button below to register a new baseline configuration profile.
                    </div>`;
                return;
            }

            // Build large vertical stack component cards (1 per row)
            data.matches.forEach(match => {
                const pct = (match.similarity * 100).toFixed(1);
                const card = document.createElement('div');
                card.className = "bg-slate-950 rounded-xl p-4 border border-slate-850 flex flex-col shadow-lg space-y-4 w-full";

                card.innerHTML = `
                    <div class="space-y-3 w-full">
                        <div class="flex justify-between items-center border-b border-slate-900 pb-2">
                            <span class="text-sm font-bold text-emerald-400 font-mono tracking-wide">${match.coral_id}</span>
                            <span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">${pct}% Match Confidence</span>
                        </div>
                        <!-- High Resolution 4:3 Aspect Safe Center Cropping Container Box -->
                        <div class="w-full aspect-[4/3] rounded-lg overflow-hidden bg-slate-900 border border-slate-950 shadow-inner">
                            <img src="${match.storage_url}" class="w-full h-full object-cover object-center hover:scale-[1.01] transition-transform duration-200" onerror="this.src='https://placehold.co'">
                        </div>
                    </div>
                    <button class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-extrabold py-3 rounded-xl shadow-md transition-all tracking-wider uppercase font-mono cursor-pointer flex items-center justify-center active:scale-[0.99]">
                        🤝 Link Verification Session to This Profile
                    </button>
                `;

                card.querySelector('button').onclick = () => {
                    executeMonitoringCommit(match.coral_id, site, match.storage_url);
                };

                listContainer.appendChild(card);
            });
        })
        .catch(() => {
            document.getElementById('loader').classList.add('hidden');
            resetDashboardState();
            showNotification("Pattern match extraction pipeline broken.", "error");
        });
};

function executeMonitoringCommit(coralId, site, storageUrl) {
    let commitForm = new FormData();
    commitForm.append('coral_id', coralId);
    commitForm.append('site_name', site);
    commitForm.append('storage_url', storageUrl);

    fetch(`${API_BASE}/commit-session`, { method: 'POST', body: commitForm })
        .then(res => res.json())
        .then(() => {
            showNotification(`Visit update session pinned to \${coralId}`, "success");
        });
}

document.getElementById('registerNewBtn').onclick = function () {
    const site = document.getElementById('siteName').value.trim();
    if (!currentFilePayload || !site) return;

    const uniqueTimestamp = Date.now().toString().slice(-4);
    const shortSiteCode = site.substring(0, 3).toUpperCase();
    const generatedCoralId = `CRL-${shortSiteCode}-${uniqueTimestamp}`;

    let regForm = new FormData();
    regForm.append('image', currentFilePayload);
    regForm.append('site_name', site);
    regForm.append('coral_id', generatedCoralId);

    this.innerText = "Processing matrix arrays...";
    this.disabled = true;

    fetch(`${API_BASE}/register-new`, { method: 'POST', body: regForm })
        .then(res => res.json())
        .then(result => {
            this.disabled = false;
            this.innerText = "➕ Log As New Colony Discovery";
            if (result.error) throw new Error(result.error);
            showNotification(`Baseline identity assigned: \${generatedCoralId}`, "success");
        })
        .catch(err => {
            this.disabled = false;
            this.innerText = "➕ Log As New Colony Discovery";
            showNotification(`New individual registration sequence failed: \${err.message}`, "error");
        });
};
