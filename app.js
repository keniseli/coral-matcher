const API_BASE = "http://localhost:8080";
let currentFilePayload = null;

// Helper to reset interface metrics
function resetDashboardState() {
    document.getElementById('statusPlaceholder').classList.remove('hidden');
    document.getElementById('matchDisplayArea').classList.add('hidden');
    document.getElementById('newCoralActionPanel').classList.add('hidden');
    document.getElementById('cardsList').innerHTML = '';
}

// Handle Image Inputs
document.getElementById('imageInput').onchange = function (e) {
    const file = e.target.files[0];
    const site = document.getElementById('siteName').value.trim();

    if (!file) return;
    if (!site) {
        alert("Please populate or select a Dive Site before selecting files.");
        document.getElementById('imageInput').value = "";
        return;
    }

    currentFilePayload = file;

    // Display localized client side preview image parameters
    document.getElementById('imagePreview').src = URL.createObjectURL(file);
    document.getElementById('previewContainer').classList.remove('hidden');
    document.getElementById('statusPlaceholder').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('matchDisplayArea').classList.add('hidden');
    document.getElementById('newCoralActionPanel').classList.add('hidden');

    let formData = new FormData();
    formData.append('image', file);
    formData.append('site_name', site);

    // Call matching engine route endpoint
    fetch(`${API_BASE}/match-coral`, { method: 'POST', body: formData })
        .then(res => {
            if (!res.ok) throw new Error("HTTP endpoint returned error configuration status.");
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
                    <div class="sm:col-span-2 p-4 bg-slate-900/60 border border-slate-700 text-slate-400 rounded-lg text-xs font-mono text-center">
                        Zero vector alignments matched within site boundaries. Click the discovery registration action button below to create a new profile baseline.
                    </div>`;
                return;
            }

            // Build individual card matrix frames
            data.matches.forEach(match => {
                const pct = (match.similarity * 100).toFixed(1);
                const card = document.createElement('div');
                card.className = "bg-slate-900 rounded-xl p-3 border border-slate-700 flex flex-col justify-between shadow-inner space-y-3";
                
                card.innerHTML = `
                    <div class="space-y-2">
                        <div class="flex justify-between items-center">
                            <span class="text-xs font-bold text-emerald-400 font-mono">${match.coral_id}</span>
                            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">${pct}% Similarity</span>
                        </div>
                        <!-- Compare baseline image straight from storage bucket -->
                        <img src="${match.storage_url}" class="w-full h-28 object-cover rounded-lg border border-slate-800" onerror="this.src='https://placehold.co'">
                    </div>
                    <button class="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-900 text-xs font-bold py-2 rounded-lg transition active:scale-95 flex items-center justify-center gap-1">
                        🤝 Link To This Individual Profile
                    </button>
                `;

                // Single-click selection event handler execution path
                card.querySelector('button').onclick = () => {
                    executeMonitoringCommit(match.coral_id, site, match.storage_url);
                };

                listContainer.appendChild(card);
            });
        })
        .catch(() => {
            document.getElementById('loader').classList.add('hidden');
            resetDashboardState();
            alert("Error contacting machine learning backend routes. Confirm serverless framework is operational.");
        });
};

// Operation Action: Save visit session log to existing verified individual profile entry
function executeMonitoringCommit(coralId, site, storageUrl) {
    let commitForm = new FormData();
    commitForm.append('coral_id', coralId);
    commitForm.append('site_name', site);
    commitForm.append('storage_url', storageUrl);

    fetch(`${API_BASE}/commit-session`, { method: 'POST', body: commitForm })
        .then(res => res.json())
        .then(() => {
            alert(`Success! Monitoring update event logged securely against individual identity record: ${coralId}`);
            location.reload();
        });
}

// Operation Action: Register completely unrecognized new coral body instance signature
document.getElementById('registerNewBtn').onclick = function() {
    const site = document.getElementById('siteName').value.trim();
    if (!currentFilePayload || !site) return;

    // Automated Individual Tracker Tag Identification Generator
    // Creates a unique identity string based on location coordinates and timestamp strings
    const uniqueTimestamp = Date.now().toString().slice(-4);
    const shortSiteCode = site.substring(0, 3).toUpperCase();
    const generatedCoralId = `CRL-${shortSiteCode}-${uniqueTimestamp}`;

    let regForm = new FormData();
    regForm.append('image', currentFilePayload);
    regForm.append('site_name', site);
    regForm.append('coral_id', generatedCoralId);

    this.innerText = "Registering baseline vector matrix...";
    this.disabled = true;

    fetch(`${API_BASE}/register-new`, { method: 'POST', body: regForm })
        .then(res => res.json())
        .then(result => {
            this.disabled = false;
            this.innerText = "➕ Record As New Discovered Colony";
            if (result.error) throw new Error(result.error);
            alert(`Success! Generated Profile Tag: ${generatedCoralId} has been saved as your new baseline reference.`);
            location.reload();
        })
        .catch(err => {
            this.disabled = false;
            this.innerText = "➕ Record As New Discovered Colony";
            alert(`Registration breakdown sequence error metrics: ${err.message}`);
        });
};
